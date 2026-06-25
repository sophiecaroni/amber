"""
    Title: Regression models pipeline

    Author: Sophie Caroni
    Date of creation: 16.04.2026

    Description:
    This script launches LMM-based regression pipelines to model reaction time and attention features.
"""
from amber.analysis import regression
from amber.viz.lmm_plots import plot_lmm_predictions


def run_rt_regression(rt_metric: str, save: bool = False, show: bool = True, verbose: bool = False) -> None:
    print(f"{(len(rt_metric) + 8) * '='}\n\t{rt_metric.upper()}\n{(len(rt_metric) + 8) * '='}")
    regression.model_rt(rt_metric_col=rt_metric, verbose=verbose, save=save)
    plot_lmm_predictions(metric=rt_metric, save=save, show=show)
    regression.rt_posthocs(rt_metric_col=rt_metric, verbose=verbose, save=save)


def run_att_regression(rt_metric: str, save: bool = False, show: bool = True, verbose: bool = False) -> None:
    label = '_mixedout'  # need _ in front!
    regression.model_att(rt_metric, verbose=verbose, save=save, label=label)
    regression.att_posthocs(rt_metric, verbose=verbose, save=save, label=label)


def run_att_vis_regression(rt_metric: str, save: bool = False, show: bool = True, verbose: bool = False) -> None:
    regression.model_att_vis(rt_metric, verbose=verbose, save=save)


def main(**kwargs):
    # run_rt_regression(**kwargs)
    # run_att_regression(**kwargs)
    run_att_vis_regression(**kwargs)


if __name__ == "__main__":
    main(
        rt_metric='rt_med_log',
        save=False,
        verbose=True,
        show=True,
    )
