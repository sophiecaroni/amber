library(dplyr)
library(tidyr)

# -------------------------
# 0. Setup and retrieve args
# -------------------------
# Extract arguments
args <- commandArgs(trailingOnly=TRUE)
rt_metric <- args[1]
df_fpath <- args[2]
verbose <- as.logical(args[3])
save <- as.logical(args[4])

# -------------------------
# 1. Load and prepare data
# -------------------------
raw_df <- read.csv(file=df_fpath, row.names=1, colClasses=c(amb_type="character"))
excluded_amb_type <- 'mixed'

# Select rows of the df where RT was aggregated as the rt_metric
att_rt_agg_val <- if (grepl("med", rt_metric)) "median" else "mean"
df <- raw_df %>%
    filter(att_rt_agg == att_rt_agg_val, amb_type != excluded_amb_type) %>%
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

# Join bl_df in df and use att_score_bl to compute the percentage of change
pct_df <- df %>%
    filter(interv_eff %in% c("ST", "FU")) %>%
    left_join(bl_df, by=c("sid", "amb_type", "eye_cond", "interv", "att_type")) %>%
    mutate(
        perc_change=(att_score - att_score_bl) / att_score_bl * 100,  # create new column with perc_change
        period=paste0("BL_", interv_eff),  # to have value BL_ST for the change between BL and ST and  BL_FU for the change between BL and FU
    ) %>%
    select(-att_score_bl, -interv_eff) %>%  # remove cols anymore needed
    drop_na(perc_change)  # nans appear when the patient did not complete one of the neede sessions

print(pct_df)
