library(dplyr)
library(tidyr)

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
att_df_fpath <- args[3]
vis_df_fpath <- args[4]
verbose <- as.logical(args[5])
save <- as.logical(args[6])

exp_label <- paste0('vis-', att_metric)
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
raw_df <- read.csv(file=att_df_fpath, row.names=1, colClasses=c(amb_type="character"))

# Select rows of the df where RT was aggregated as the rt_metric
att_rt_agg_val <- if (grepl("med", rt_metric)) "median" else "mean"
df <- raw_df %>%
    filter(att_rt_agg == att_rt_agg_val, att_type == att_metric) %>%
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

# -------------------------------------------------------
# 2. Format baseline-attention score as separate column
# -------------------------------------------------------
# Subset df to baseline observations, and rename att_score column into att_score_bl
bl_df <- df %>%
    filter(interv_eff == "BL") %>%
    select(sid, amb_type, eye_cond, interv, att_type, att_score_bl=att_score)  # rename att_score col into att_score_bl

# Join bl_df in df to have baseline values as a new column (and not a level of interv_eff column) to use as covariate
df <- df %>%
    filter(interv_eff %in% c("ST", "FU")) %>%  # drop the baseline rows; baseline is now carried in att_score_bl col
    mutate(interv_eff = droplevels(interv_eff)) %>%  # need to also drop the BL as level
    left_join(bl_df, by=c("sid", "amb_type", "eye_cond", "interv", "att_type")) %>%
    drop_na(att_score, att_score_bl)  # nans appear when the patient did not complete one of either BL or ST/FU sessions
