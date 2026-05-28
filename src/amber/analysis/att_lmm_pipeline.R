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
        att_change=att_score - att_score_bl,  # create new column with att_change (attentional change from baseline)
        period=paste0("BL_", interv_eff),  # to have value BL_ST for the change between BL and ST and  BL_FU for the change between BL and FU
    ) %>%
    select(-att_score_bl, -interv_eff, -att_score) %>%  # remove cols anymore needed
    drop_na(att_change)  # nans appear when the patient did not complete one of the sessions needed for computation

