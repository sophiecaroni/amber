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

if (save) {
    dir.create(wd, recursive = TRUE, showWarnings = FALSE)
    figures_dir <- file.path(project_root, "outputs", "figures", "LMM")
    dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)
    log_con <- file(file.path(wd, paste0("report", "_", att_metric, '.txt')), open = "wt")
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
    select(-att_rt_agg, -group, -tpoint) %>%  # dont include cols not needed
    mutate(
        sid=factor(sid),
        att_type=factor(att_type),
        amb_type=factor(amb_type),
        eye_cond=factor(eye_cond),
        interv=factor(interv),
        interv_eff=factor(interv_eff),
        age=as.numeric(age),
        att_score=as.numeric(att_score),
    )

# Compute the percentage of change of attention features from BL to ST and from BL to FU
bl_df <- df %>%
    filter(interv_eff == "BL") %>%
    select(sid, amb_type, eye_cond, interv, att_type, att_score_bl=att_score)  # rename att_score col into att_score_bl

# Join bl_df in df and use att_score_bl to compute the (absolute) change in attention
df <- df %>%
    filter(interv_eff %in% c("ST", "FU")) %>%
    left_join(bl_df, by=c("sid", "amb_type", "eye_cond", "interv", "att_type")) %>%  # create a att_score_bl col with BL values relative to the grouping vars
    mutate(
        bl_change=att_score - att_score_bl,  # create new column bl_change (attentional change from baseline)
        period=factor(paste0("BL_", interv_eff)),  # to have value BL_ST for the change between BL and ST and  BL_FU for the change between BL and FU
    ) %>%
    select(-att_score_bl, -interv_eff, -att_score) %>%  # remove cols anymore needed
    drop_na(bl_change)  # nans appear when the patient did not complete one of the sessions needed for computation

# Check normality of the dependent variable via a QQ plot
if (save) {
    png(file.path(figures_dir, paste0("qq", "_", att_metric, ".png")))
    qqPlot(df$bl_change)
    invisible(dev.off())  # write file and close figure
}
if (save) {
    png(file.path(figures_dir, paste0("hist", "_", att_metric, ".png")))
    hist(df$bl_change)
    invisible(dev.off())  # write file and close figure
}

# -------------------------
# 2. Define nested models
# -------------------------

# Random effects structure: random intercepts and random slopes for period and eye_cond, both varying by subject
random_terms <- "(1 | sid)"

formulas <- list(

    # Full model: all interactions up to 4-way among primary factors + all main effects + age covariate
    m_full = as.formula(paste(
        "bl_change ~ amb_type * eye_cond * interv * period +",  # * expands to all interactions up to 4-way, equivalent to (sum of all factors)^4
        "age +", random_terms)),

    # Model without 4-way interaction: all interactions up to 3-way among primary factors + all main effects + age covariate
    m_no_4way = as.formula(paste(
        "bl_change ~ (amb_type + eye_cond + interv + period)^3 +",
        "age +", random_terms)),

    # Model without 3-way interaction: all interactions up to 2-way among primary factors + all main effects + age covariate
    m_no_3way = as.formula(paste(
        "bl_change ~ (amb_type + eye_cond + interv + period)^2 +",
        "age +", random_terms)),

    # Model with main effects only
    m_main = as.formula(paste(
        "bl_change ~ amb_type + eye_cond + interv + period + age +",
        random_terms))
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
converged <- function(model) is.null(model@optinfo$conv$lme4$messages)

cat("\n--- Check of model validity ---\n")
for (name in model_names) {
    cat(name, "— converged:", converged(models[[name]]), "| singular:", isSingular(models[[name]]), "\n")
}

valid <- function(model) converged(model) && !isSingular(model)  # a model is valid if it converged and its random effects structure is not degenerate
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
  png(file.path(figures_dir, paste0("fitted_vs_residuals", "_", att_metric, ".png")))
  plot(model_to_interpret)
  invisible(dev.off())  # write file and close figure

  # QQ plot
  png(file.path(figures_dir, paste0("qq", "_", att_metric, "_residuals", ".png")))
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
    output_df_path <- file.path(wd, paste0("results_", att_metric, ".csv"))
    write.csv(df, output_df_path, row.names=FALSE)

    # Save the ANOVA results
    anova_df <- as.data.frame(anova_result)
    anova_df <- rename(anova_df, p_val = `Pr(>Chisq)`)  # rename automatic p value col; need ` because it contains special characters
    anova_path <- file.path(wd, paste0("anova_", att_metric, ".csv"))
    write.csv(anova_df, anova_path, row.names=TRUE)  # use row names to have a column with the effects

    # Save the mixed model
    saveRDS(model_to_interpret, file.path(wd, paste0("model_", att_metric, ".rds")))
}
