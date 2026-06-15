library(dplyr)
library(tidyr)
library(car)
library(lme4)

# -------------------------
# 0. Setup and retrieve args
# -------------------------
# Setup working and saving directories
script_dir <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(trailingOnly=FALSE), value=TRUE)[1])))
project_root <- dirname(dirname(dirname(script_dir)))
wd <- file.path(project_root, "outputs", "stats")
setwd(wd)

# Extract arguments
args <- commandArgs(trailingOnly=TRUE)
rt_metric <- args[1]
att_metric <- args[2]
df_fpath <- args[3]
verbose <- as.logical(args[4])
save <- as.logical(args[5])

exp_label <- paste0(att_metric, args[6])
if (save) {
    dir.create(wd, recursive = TRUE, showWarnings = FALSE)
    figures_dir <- file.path(project_root, "outputs", "figures", "LMM")
    dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)
    log_con <- file(file.path(wd, paste0("report", "_", exp_label, '.txt')), open = "wt")
    sink(log_con, split = TRUE)  # print/cat outputs
    sink(log_con, type = "message")  # warnings
    on.exit({ sink(type = "message"); sink(); close(log_con) }, add = TRUE)  # use on.exit to run the teardown regardless of how the script exits (error or normal)
}

# -------------------------
# 1. Load and prepare data
# -------------------------
raw_df <- read.csv(file=df_fpath, row.names=1, colClasses=c(amb_type="character"))
excluded_amb_type <- 'mixed'

# Select rows of the df where RT was aggregated as the rt_metric
att_rt_agg_val <- if (grepl("med", rt_metric)) "median" else "mean"
df <- raw_df %>%
    filter(att_rt_agg == att_rt_agg_val, amb_type != excluded_amb_type, att_type == att_metric) %>%
    mutate(
        sid=factor(sid),
        att_type=factor(att_type),
        amb_type=factor(amb_type),
        eye_cond=factor(eye_cond),
        interv=factor(interv),
        interv_eff=factor(interv_eff),
        age=as.numeric(age),
        att_score=as.numeric(att_score),
        order=factor(case_when(
            tpoint %in% c("T1", "T2") ~ "first",
            tpoint %in% c("T4", "T5") ~ "second",
            tpoint == "T3" & interv_eff == "FU" ~ "first",
            tpoint == "T3" & interv_eff == "BL" ~ "second",
        )),
    ) %>%
    select(-att_rt_agg, -group, -tpoint)  # dont include cols not needed

# Subset df to baseline observations
bl_df <- df %>%
    filter(interv_eff == "BL") %>%
    select(sid, amb_type, eye_cond, interv, att_type, att_score_bl=att_score)  # rename att_score col into att_score_bl

# Join bl_df in df and use att_score_bl to compute the (absolute) change in attention
df <- df %>%
    filter(interv_eff %in% c("ST", "FU")) %>%  # drop the baseline rows; baseline is now carried in att_score_bl col
    mutate(interv_eff = droplevels(interv_eff)) %>%  # need to also drop the BL as level
    left_join(bl_df, by=c("sid", "amb_type", "eye_cond", "interv", "att_type")) %>%
    drop_na(att_score, att_score_bl)  # nans appear when the patient did not complete one of the sessions needed for computation

# Check normality of the dependent variable via plots
y <- "att_score"

if (save) {
    png(file.path(figures_dir, paste0("qq", "_", exp_label, ".png")))
    qqPlot(df[[y]])
    invisible(dev.off())  # write file and close figure
}
if (save) {
    png(file.path(figures_dir, paste0("hist", "_", exp_label, ".png")))
    hist(df[[y]])
    invisible(dev.off())  # write file and close figure
}

# -------------------------
# 2. Define nested models
# -------------------------

# Random effect terms
random_terms <- "+ (1 | sid)"

# Covariate terms
cov_terms <- "+ age + att_score_bl + order * interv"

formulas <- list(

    # Full model: all interactions up to 4-way among primary factors + all main effects + age covariate
    m_full = as.formula(paste(
        y, "~ amb_type * eye_cond * interv * interv_eff",  # * expands to all interactions up to 4-way, equivalent to (sum of all factors)^4
        cov_terms, random_terms)),

    # Model without 4-way interaction: all interactions up to 3-way among primary factors + all main effects + age covariate
    m_no_4way = as.formula(paste(
        y, "~ (amb_type + eye_cond + interv + interv_eff)^3",
        cov_terms, random_terms)),

    # Model without 3-way interaction: all interactions up to 2-way among primary factors + all main effects + age covariate
    m_no_3way = as.formula(paste(
        y, "~ (amb_type + eye_cond + interv + interv_eff)^2",
        cov_terms, random_terms)),

    # Model with main effects only
    m_main = as.formula(paste(
        y, "~ amb_type + eye_cond + interv + interv_eff",
        cov_terms, random_terms))
)

# -------------------------
# 3. Fit nested models
# -------------------------
reml <- FALSE  # for parameters estimation; "ML (REML = FALSE) should be used if you decide to use likelihood ratio tests to test fixed effects"  https://www.zoology.ubc.ca/~schluter/R/Model.html
model_names <- names(formulas)
models <- vector("list", length(formulas))
names(models) <- model_names
for (name in model_names) {
    models[[name]] <- lmer(formulas[[name]], data = df, REML = reml)  # fit each nested model
    if (verbose) {
        cat('SUMMARY OF', name, ':\n')
        print(summary(models[[name]], correlations=TRUE))
    }
}


# -------------------------
# 4. Verify model validity
# -------------------------
converged <- function(model) {
    msgs <- model@optinfo$conv$lme4$messages
    msgs <- msgs[!grepl("singular", msgs, ignore.case = TRUE)]  # ignore automatic singularity detection done here
    length(msgs) == 0
}

cat("\n--- Check of model validity ---\n")
has_degenerate_corrs <- function(model) {
    rand_eff_cov_structure <- as.data.frame(VarCorr(model))
    corrs <- rand_eff_cov_structure$sdcor[!is.na(rand_eff_cov_structure$var2)]  # random-effect correlations, where SD (var2) are not nans
    any(abs(corrs) > 1 - 1e-4, na.rm = TRUE)  # na.rm: a NaN correlation means its variance is ~0 (benign), not degenerate
}
for (name in model_names) {
    cat(
        name, "— converged:", converged(models[[name]]),
        "| singular:", isSingular(models[[name]]),
        "| degenerate corrs:", has_degenerate_corrs(models[[name]]),
        "\n"
    )
}
valid <- function(model) converged(model) && (!isSingular(model) || !has_degenerate_corrs(model))
valid_models <- Filter(valid, models)

# Quit if no model is valid
if (length(valid_models) == 0) {
    cat("\nSELECTED_MODEL=No valid model found !\n")
    quit(save="no")
}


# -------------------------
# 5. Select best model
# -------------------------

# Initialise best_model to most complex model (first in valid_models)
model_names <- names(valid_models)
best_model <- model_names[1]

# If only one model was valid, select it as best model
if (length(valid_models) == 1) {
    cat("\nSELECTED_MODEL=", best_model, "\n", sep = "")

# If multiple models where valid, run LRT pairwise comparison between models
} else {

    # Run LRT between consecutive valid models, stepping down to less complext model if not significant
    for (i in seq_len(length(valid_models) - 1)) {
        name_complex <- model_names[i]
        name_simpler <- model_names[i + 1]

        cat("\n--- LRT:", name_complex, "(complex) vs", name_simpler, "(simpler) ---\n")
        complex_model = valid_models[[i]]
        simpler_model = valid_models[[i + 1]]
        lrt <- anova(complex_model, simpler_model, test = 'LRT')
        print(lrt)
        p <- tryCatch(lrt$`Pr(>Chisq)`[2], error = function(e) NA_real_)

        if (is.na(p) || p >= 0.05) {
            best_model <- name_simpler  # no significant difference, step down to simpler model
        } else {
            break  # significant difference, keep the most complex model
        }
    }
    cat("\nSELECTED_MODEL=", best_model, "\n", sep = "")
}

model_to_interpret <- models[[best_model]]


# -------------------------
# 5. Diagnostics on selected model
# -------------------------

# Check correct structure of random effects
cat("\n--- Random effects: selected model ---\n")
print(VarCorr(model_to_interpret))  # if (all) intercept-slope correlations are near 0, || (uncorrelated slopes) would be equally appropriate

# Check residuals normality
if (save) {
  # Fitted vs residuals — checks homoscedasticity
  png(file.path(figures_dir, paste0("fitted_vs_residuals", "_", exp_label, ".png")))
  plot(model_to_interpret)
  invisible(dev.off())  # write file and close figure

  # QQ plot
  png(file.path(figures_dir, paste0("qq", "_", exp_label, "_residuals", ".png")))
  qqPlot(residuals(model_to_interpret))
  invisible(dev.off())  # write file and close figure
}

# -------------------------
# 6. Inference on the selected model
# -------------------------

# If Type III fails on the selected model (e.g. aliased coefficients due to rank deficiency), fall back to simpler models
best_idx <- match(best_model, names(models))
fallback_models <- if (best_idx < length(models)) models[(best_idx + 1):length(models)] else list()

# Run Type III Wald chi-square tests to identify which predictors/interactions have a significant effect
cat("\n--- Type III tests: selected model ---\n")
anova_result <- tryCatch(
  car::Anova(model_to_interpret, type = "III"),
  error = function(e) {
    cat("Note: Type III failed on selected model (aliased coefficients), trying fallbacks.\n")
    result <- NULL
    for (m in fallback_models) {
      result <- tryCatch(car::Anova(m, type = "III"), error = function(e) NULL)
      if (!is.null(result)) break
    }
    result
  }
)
print(anova_result)

# Add model prediction lines over data
df$fitted <- predict(model_to_interpret)

if (save) {
    # Save the input dataframe with the predicted att_metric results
    output_df_path <- file.path(wd, paste0("results_", exp_label, ".csv"))
    write.csv(df, output_df_path, row.names=FALSE)

    # Save the ANOVA results
    anova_df <- as.data.frame(anova_result)
    anova_df <- rename(anova_df, p_val = `Pr(>Chisq)`)  # rename automatic p value col; need ` because it contains special characters
    anova_path <- file.path(wd, paste0("anova_", exp_label, ".csv"))
    write.csv(anova_df, anova_path, row.names=TRUE)  # use row names to have a column with the effects

    # Save the model
    saveRDS(model_to_interpret, file.path(wd, paste0("model_", exp_label, ".rds")))
}
