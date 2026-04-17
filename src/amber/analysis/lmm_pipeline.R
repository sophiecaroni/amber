library(lme4)
library(car)
library(emmeans)
library(dplyr)

script_dir <- dirname(normalizePath(sub("--file=", "", grep("--file=", commandArgs(trailingOnly=FALSE), value=TRUE)[1])))
project_root <- dirname(dirname(dirname(script_dir)))
wd <- file.path(project_root, "outputs", "stats")
setwd(wd)

# -------------------------
# 0. Retrieve args
# -------------------------
args <- commandArgs(trailingOnly = TRUE)
metric <- args[1]
df_fpath <- args[2]

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
#
# Notes.
# - (1 + interv_eff | sid): both random intercept AND random slope for interv_eff vary by subject, as we assume subjects
#                           start at different baseline RT (intercept) and subjects improve at different rates over
#                           time (slope).
# - (1 + eye_cond | sid): both random intercept AND random slope for eye_cond vary by subject, as we assume subjects have
#                         different baseline RT for each eye (intercept) and amblyopia affects the dofference between
#                         dominant and non-dominant eyes differently.
# -------------------------

# Full model: all interactions up to 4-way among primary factors + all main effects + age covariate
full_formula <- y ~ amb_type * eye_cond * interv * interv_eff  # * is equal as doing (sum of all factors)^4
                    + age
                    + (1 + interv_eff | sid)
                    + (1 + eye_cond | sid)

# no-4-way: all interactions up to 3-way among primary factors + all main effects + age covariate
no_4way_formula <- y ~ (amb_type + eye_cond + interv + interv_eff)^3  # syntax needed to exclude the 4-way interaction
                        + age
                        + (1 + interv_eff | sid)
                        + (1 + eye_cond | sid)

# Main effects only
main_formula <- y ~ amb_type + eye_cond + interv + interv_eff + age
                    + (1 + interv_eff | sid)
                    + (1 + eye_cond | sid)

# -------------------------
# 3. Fit nested models
# -------------------------
m_full <- lmer(full_formula, data = df, REML = FALSE)

m_no_4way <- lmer(no_4way_formula, data = df, REML = FALSE)

m_main <- lmer(main_formula, data = df, REML = FALSE)


# -------------------------
# 4. Model decision
# -------------------------

# Compute AI
cat("\n--- AIC comparison ---\n")
print(AIC(m_full, m_no_4way, m_main))

# Run likelihood-ratio test to verify if removing the 4-way interaction is significant
cat("\n--- ANOVA: Full vs no-4-way ---\n")
full_vs_no4 <- anova(m_full, m_no_4way)
print(full_vs_no4)
p_full_vs_no4 <- tryCatch(full_vs_no4$`Pr(>Chisq)`[2], error = function(e) NA_real_)  # get p-values

# Run likelihood-ratio test to verify if removing the all interactions up to 3-way is significant
cat("\n--- ANOVA: no-4-way vs main effects ---\n")
no4_vs_main <- anova(m_no_4way, m_main)
print(no4_vs_main)
p_no4_vs_main <- tryCatch(no4_vs_main$`Pr(>Chisq)`[2], error = function(e) NA_real_)  # get p-values

# Initialise best_model to most complex model
best_model <- "m_full"  

# Chose no-4-way model over full model if their likelihood-ratio test didn't detect a difference
if (!is.na(p_full_vs_no4) && p_full_vs_no4 >= 0.05) { 
  best_model <- "m_no_4way"
}

# Chose main model over no-4-way  if their likelihood-ratio test didn't detect a difference
if (best_model == "m_no_4way" && !is.na(p_no4_vs_main) && p_no4_vs_main >= 0.05) {  # only test if no-4-way was selected in the previous step
  best_model <- "m_main"
}

cat("\nSELECTED_MODEL=", best_model, "\n", sep = "")

model_to_interpret <- switch(
  best_model,
  m_full = m_full,
  m_no_4way = m_no_4way,
  m_main = m_main
)

# -------------------------
# 5. Residual diagnostics on selected model
# -------------------------

# Fitted vs residuals — checks homoscedasticity
plot(model_to_interpret)

# QQ plot — checks normality of residuals
qqnorm(residuals(model_to_interpret))
qqline(residuals(model_to_interpret))

