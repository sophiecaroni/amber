"""
    Title: Linear mixed models (LMM) pipeline

    Author: Sophie Caroni
    Date of creation: 16.04.2026

    Description:
    This script launches a LMM pipeline to model reaction time at the trial level.
"""
import amber.analysis.lmm as lmm


def run_lmm_pipeline() -> None:
    metrics = (
        "rt_med",
        "rt_mean",
    )

    for metric in metrics:
        lmm.run_lmm_testing(rt_metric_col=metric)
        lmm.test(rt_metric_col=metric)


if __name__ == "__main__":
    run_lmm_pipeline()
