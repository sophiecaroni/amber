"""
    Title: Linear mixed models (LMM) pipeline

    Author: Sophie Caroni
    Date of creation: 16.04.2026

    Description:
    This script launches LMM pipelines to model reaction time and attention features.
"""
import amber.analysis.lmm as lmm
from amber.viz.lmm_plots import plot_lmm_predictions


def run_rt_lmm(rt_metric: str, save: bool = False, show: bool = True, verbose: bool = False) -> None:
    print(f"\n####################################### {rt_metric} #######################################\n")
    lmm.rt_lmm(rt_metric_col=rt_metric, verbose=verbose, save=save)
    plot_lmm_predictions(metric=rt_metric, save=save, show=show)
    lmm.rt_post_hocs(rt_metric_col=rt_metric, verbose=verbose, save=save)


def run_att_lmm(rt_metric: str, save: bool = False, show: bool = True, verbose: bool = False) -> None:
    lmm.att_lmm(rt_metric, verbose=verbose, save=save)


def main(**kwargs):
    # run_rt_lmm(**kwargs)
    run_att_lmm(**kwargs)


if __name__ == "__main__":

    main(
        rt_metric='rt_med_log',
        save=False,
        verbose=True,
        show=True,
    )
