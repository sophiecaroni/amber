"""
    Title: Linear mixed models (LMM) pipeline

    Author: Sophie Caroni
    Date of creation: 16.04.2026

    Description:
    This script launches a LMM pipeline to model reaction time at the trial level.
"""
import amber.analysis.lmm as lmm
from amber.viz.lmm_plots import plot_lmm_predictions


def run_lmm_pipeline(save: bool = False, show: bool = True, verbose: bool = False) -> None:
    metrics = (
        "rt_med",
        "rt_mean",
        "rt_med_log",
        "rt_mean_log",
    )

    for metric in metrics:
        print(f"\n####################################### {metric} #######################################\n")
        # fit_method = lmm.select_best_fit_method(rt_metric_str=metric)
        lmm.test(rt_metric_col=metric, verbose=verbose, save=save)
        plot_lmm_predictions(metric=metric, save=save, show=show)
        lmm.post_hocs(rt_metric_col=metric, verbose=verbose, save=save)


if __name__ == "__main__":
    run_lmm_pipeline(
        save=False,
        verbose=False,
        show=True,
    )
