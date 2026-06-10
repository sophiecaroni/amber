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
metric <- args[1]
anova_fpath <- args[2]
model_fpath <- args[3]
verbose <- as.logical(args[4])
save <- as.logical(args[5])

# -------------------------
# 1. Load and prepare data
# -------------------------

# MIXED MODEL
model <- readRDS(model_fpath)
print('MIXED MODEL RESULTS:')
print(summary(model, correlations=TRUE))

# ANOVA
raw_anova_df <- read.csv(anova_fpath)
anova_df <- raw_anova_df %>%
    rename(effect=X) %>% # Rename
    mutate(
        effect=factor(effect),
        p_val=as.numeric(p_val),
    )
print('ANOVA RESULTS:')
print(anova_df)

# -------------------------
# 2. Compute estimated marginal means (EMMs)
# -------------------------

# Define function to sort interaction effect terms alphabetically
sort_int_term <- function(term) paste(sort(trimws(strsplit(term, ":")[[1]])), collapse=":")

# Define function to define whether an interaction is significant in ANOVA
int_is_sign <- function(...) {
    term <- paste(sort(c(...)), collapse=":")
    term %in% sapply(as.character(anova_df$effect)[anova_df$p_val < 0.05], sort_int_term)
}

if (int_is_sign("amb_type", "eye_cond", "interv", "interv_eff")) {

    # Comparison of primary interest: VR pre vs. post and pre vs. follow-up in ND for each amblyopia type
    emm <- emmeans(model, ~ interv_eff | amb_type | eye_cond | interv, type="response")  # response transforms back from log into original scale

    emm_full <- emmeans(model, ~ interv_eff * interv | amb_type | eye_cond, type="response")
}

# -------------------------
# 3. Run post-hoc tests
# -------------------------
if (int_is_sign("amb_type", "eye_cond", "interv", "interv_eff")) {

    cat("\n--- emmeans: 1) interv_eff (VR and OA separately) separately for each intervention type (only against BL), eye condition and amblyopia type ---\n")
    contrasts_trt <- contrast(
        regrid(emm),  # regrid to report in absolute ms; otherwise we get ratios i.e. interpret "RT at BL was 15.3% higher than at FU"
        method="trt.vs.ctrl", ref="BL"  # this to compare a reference ref (control, here baseline "BL") to all other levels, skipping levels between each other
    )
    print(contrasts_trt)

    cat("\n--- emmeans: 2) both interv and interv_eff focal, all pairs ---\n")
    contrasts_pairs <- pairs(  # shortcut for contrast(intervention='pairwise')
        regrid(emm_full),  # regrid to report in absolute ms; otherwise we get ratios i.e. interpret "RT at BL was 15.3% higher than at FU"
    )
    print(contrasts_pairs)
}

if (save) {
    stats_dir <- file.path(project_root, "outputs", "stats")
    dir.create(stats_dir, recursive = TRUE, showWarnings = FALSE)

    write.csv(as.data.frame(contrasts_trt),   file.path(stats_dir, paste0("posthocs_interv_bl_ref_", metric, ".csv")),   row.names=FALSE)
    write.csv(as.data.frame(contrasts_pairs), file.path(stats_dir, paste0("posthocs_intervxeff_pairs_", metric, ".csv")), row.names=FALSE)
}
