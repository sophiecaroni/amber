library(dplyr)
library(emmeans)

# -------------------------
# 0. Setup and retrieve args
# -------------------------
# Setup working and saving directories
script_dir <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(trailingOnly=FALSE), value=TRUE)[1])))
project_root <- dirname(dirname(dirname(script_dir)))

# Extract arguments
args <- commandArgs(trailingOnly=TRUE)
att_metric <- args[1]
anova_fpath <- args[2]
model_fpath <- args[3]
verbose <- as.logical(args[4])
save <- as.logical(args[5])

exp_label <- paste0(att_metric, args[6])

if (save) {
    stats_dir <- file.path(project_root, "outputs", "stats")
    dir.create(stats_dir, recursive = TRUE, showWarnings = FALSE)
}

# -------------------------
# 1. Load and prepare data
# -------------------------

# MIXED MODEL
model <- readRDS(model_fpath)
cat('\nMIXED MODEL RESULTS:\n')
print(summary(model, correlations=TRUE))

# ANOVA
raw_anova_df <- read.csv(anova_fpath)
anova_df <- raw_anova_df %>%
    rename(effect=X) %>% # Rename
    mutate(
        effect=factor(effect),
        p_val=as.numeric(p_val),
    )
cat('\nANOVA RESULTS:\n')
print(anova_df)

# -------------------------
# 2. Compute estimated marginal means (EMMs)
# -------------------------

# Sort an interaction term's factors alphabetically so terms match regardless of operand order
sort_int_term <- function(term) paste(sort(trimws(strsplit(term, ":")[[1]])), collapse=":")

# Whether the given interaction term is significant in the ANOVA (order-insensitive match)
int_is_sign <- function(...) {
    term <- paste(sort(c(...)), collapse=":")
    term %in% sapply(as.character(anova_df$effect)[anova_df$p_val < 0.05], sort_int_term)
}

# Comparison of primary interest: the new (VR) vs. the old (OA) intervention, by order if interv:order is significant
df <- model@frame  # need this for emmeans to recover data stored in model's call (fitted on literally 'df')
sign_int <- int_is_sign("interv", "order")
emm_interv <- if (sign_int) emmeans(model, ~ interv | order) else emmeans(model, ~ interv)
emm_interv_label <- if (sign_int) "intervxorder" else "interv"

# -------------------------
# 3. Run post-hoc tests
# -------------------------

stats_dir <- file.path(project_root, "outputs", "stats")

cat("\nEMMEANS: VR vs OA", if (sign_int) "within each intervention order" else "(marginal)", "\n\n")
contrasts_interv <- summary(
    contrast(regrid(emm_interv), method="pairwise"),  # VR vs OA; regrid to report on the absolute (response) scale, not ratios
    infer=c(TRUE, TRUE),  # report both the 95% CIs and the p-values
    side="<"  # one-sided test of the a priori hypothesis VR > OA: contrast is OA - VR, so VR better means OA - VR < 0
)
print(contrasts_interv)

if (save) {
    write.csv(as.data.frame(contrasts_interv), file.path(stats_dir, paste0("posthocs_", emm_interv_label, "_", exp_label, ".csv")), row.names=FALSE)
}

if (sign_int) {  # Complementary view of the same interaction: effect of order WITHIN each intervention
    emm_order <- emmeans(model, ~ order | interv)
    contrasts_order <- summary(contrast(regrid(emm_order), method="pairwise"), infer=c(TRUE, TRUE))
    print(contrasts_order)

    if (save) {
        write.csv(as.data.frame(contrasts_order), file.path(stats_dir, paste0("posthocs_orderxinterv_", exp_label, ".csv")), row.names=FALSE)
    }
}


