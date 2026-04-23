library(lme4)
library(car)
library(emmeans)
library(dplyr)

# -------------------------
# 0. Setup and retrieve args
# -------------------------
# Setup working and saving directories
script_dir <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(trailingOnly=FALSE), value=TRUE)[1])))
project_root <- dirname(dirname(dirname(script_dir)))
wd <- file.path(project_root, "outputs", "stats")
dir.create(wd, recursive = TRUE, showWarnings = FALSE)
setwd(wd)

# Extract arguments
args <- commandArgs(trailingOnly = TRUE)
metric <- args[1]
df_fpath <- args[2]
save <- as.logical(args[3])

if (save) {
  figures_dir <- file.path(project_root, "outputs", "figures", "LMM")
  dir.create(figures_dir, recursive = TRUE, showWarnings = FALSE)
}

if (save) {
  log_con <- file(file.path(wd, paste0("report", "_", metric, '.txt')), open = "wt")
  sink(log_con, split = TRUE)  # print/cat outputs
  sink(log_con, type = "message")  # warnings
  on.exit({ sink(type = "message"); sink(); close(log_con) }, add = TRUE)  # use on.exit to run the teardown regardless of how the script exits (error or normal)
}

# -------------------------
# 1. Load and prepare data
# -------------------------
raw_df <- read.csv(file = df_fpath, row.names = 1, colClasses = c(amb_type = "character"))

df <- raw_df %>%
  select(sid, amb_type, eye_cond, interv, interv_eff, age, all_of(metric)) %>%  # select columns of interest for this analysis
  rename(y = all_of(metric)) %>%  # Rename
  mutate(
    sid = factor(sid),
    amb_type = factor(amb_type),
    eye_cond = factor(eye_cond),
    interv = factor(interv),
    interv_eff = factor(interv_eff),
    age = as.numeric(age),  # age as continuous covariate, not a factor
  )

# -------------------------
# 2. Define nested models
# -------------------------

# Random effects structure: random intercepts and random slopes for interv_eff and eye_cond, both varying by subject
random_terms <- "(1 + interv_eff | sid) + (1 + eye_cond | sid)"

# Full model: all interactions up to 4-way among primary factors + all main effects + age covariate
full_formula <- as.formula(paste(
  "y ~ amb_type * eye_cond * interv * interv_eff +",  # * expands to all interactions up to 4-way, equivalent to (sum of all factors)^4
  "age +", random_terms
))

# no-4-way: all interactions up to 3-way among primary factors + all main effects + age covariate
no_4way_formula <- as.formula(paste(
  "y ~ (amb_type + eye_cond + interv + interv_eff)^3 +",
  "age +", random_terms
))

# no-3-way: all interactions up to 2-way among primary factors + all main effects + age covariate
no_3way_formula <- as.formula(paste(
  "y ~ (amb_type + eye_cond + interv + interv_eff)^2 +",
  "age +", random_terms
))

# Main effects only
main_formula <- as.formula(paste(
  "y ~ amb_type + eye_cond + interv + interv_eff + age +",
  random_terms
))

# -------------------------
# 3. Fit nested models
# -------------------------
reml <- FALSE
ctrl <- lmerControl(optimizer = "bobyqa", optCtrl = list(maxfun = 2e5))  # increase iterations to improve convergence

m_full <- lmer(full_formula, data = df, REML = reml, control = ctrl)
m_no_4way <- lmer(no_4way_formula, data = df, REML = reml, control = ctrl)
m_no_3way <- lmer(no_3way_formula, data = df, REML = reml, control = ctrl)
m_main <- lmer(main_formula, data = df, REML = reml, control = ctrl)

converged <- function(model) is.null(model@optinfo$conv$lme4$messages)
valid <- function(model) converged(model) && !isSingular(model)  # a model is valid if it converged and its random effects structure is not degenerate

cat("\n--- Convergence and singularity check ---\n")
cat("m_full — converged:", converged(m_full), "| singular:", isSingular(m_full),    "\n")
cat("m_no_4way — converged:", converged(m_no_4way), "| singular:", isSingular(m_no_4way), "\n")
cat("m_no_3way — converged:", converged(m_no_3way), "| singular:", isSingular(m_no_3way), "\n")
cat("m_main — converged:", converged(m_main), "| singular:", isSingular(m_main), "\n")


# -------------------------
# 4. Best model selection
# -------------------------

# Run likelihood-ratio test (LRT) to verify if removing the 4-way interaction is significant
cat("\n--- LRT: Full vs no-4-way ---\n")
full_vs_no4 <- anova(m_full, m_no_4way, test='LRT')
print(full_vs_no4)
p_full_vs_no4 <- tryCatch(full_vs_no4$`Pr(>Chisq)`[2], error = function(e) NA_real_)  # get p-values

# Run LRT to verify if removing 3-way interactions is significant
cat("\n--- LRT: no-4-way vs no-3-way ---\n")
no4_vs_no3 <- anova(m_no_4way, m_no_3way)
print(no4_vs_no3)
p_no4_vs_no3 <- tryCatch(no4_vs_no3$`Pr(>Chisq)`[2], error = function(e) NA_real_)

# Run LRT to verify if removing 2-way interactions is significant
cat("\n--- LRT: no-3-way vs main effects ---\n")
no3_vs_main <- anova(m_no_3way, m_main)
print(no3_vs_main)
p_no3_vs_main <- tryCatch(no3_vs_main$`Pr(>Chisq)`[2], error = function(e) NA_real_)

# Initialise best_model to most complex model
best_model <- "m_full"

# Step down if m_full is not valid or if LRT didn't detect a difference to no-4-way
if (!valid(m_full) || is.na(p_full_vs_no4) || p_full_vs_no4 >= 0.05) {
  best_model <- "m_no_4way"
}
# If no-4way was previously selected, step down if m_no_4way is not valid or if LRT didn't detect a difference to no-3-way
if (best_model == "m_no_4way" && (!valid(m_no_4way) || is.na(p_no4_vs_no3) || p_no4_vs_no3 >= 0.05)) {
  best_model <- "m_no_3way"
}
# If no-3-way was previously selected, step down if m_no_3way is not valid or if LRT didn't detect a difference not valid main
if (best_model == "m_no_3way" && (!valid(m_no_3way) || is.na(p_no3_vs_main) || p_no3_vs_main >= 0.05)) {
  best_model <- "m_main"
}
# Warn if even the simplest model is not valid — results should not be trusted
if (best_model == "m_main" && !valid(m_main)) {
  cat("WARNING: even the main effects model failed to converge or is singular.\n")
}

cat("\nSELECTED_MODEL=", best_model, "\n", sep = "")
model_to_interpret <- switch(
  best_model,
  m_full = m_full,
  m_no_4way = m_no_4way,
  m_no_3way = m_no_3way,
  m_main = m_main
)

# -------------------------
# 5. Diagnostics on selected model
# -------------------------

# Check correct structure of random effects
cat("\n--- Random effects: selected model ---\n")
print(VarCorr(model_to_interpret))  # if (all) intercept-slope correlations are near 0, || (uncorrelated slopes) would be equally appropriate

# Check residuals normality
if (save) {
  # Fitted vs residuals — checks homoscedasticity
  png(file.path(figures_dir, paste0("fitted_vs_residuals", "_", metric, ".png")))
  plot(model_to_interpret)
  invisible(dev.off())  # write file and close figure

  # QQ plot — checks normality of residuals
  png(file.path(figures_dir, paste0("qq", "_", metric, ".png")))
  qqnorm(residuals(model_to_interpret))
  qqline(residuals(model_to_interpret))
  invisible(dev.off())  # write file and close figure
}

# -------------------------
# 6. Inference on the selected model
# -------------------------

# If Type III fails on the selected model (e.g. aliased coefficients due to rank deficiency), fall back to simpler models
fallback_models <- switch(
  best_model,
  m_full = list(m_no_4way, m_no_3way, m_main),
  m_no_4way = list(m_no_3way, m_main),
  m_no_3way = list(m_main),
  m_main = list()
)

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