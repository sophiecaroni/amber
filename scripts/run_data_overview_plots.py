import amber_utils.io_utils as io
import amber.viz.data_viz as vp
import numpy as np


def run_data_overview_plots(show: bool, save: bool = False):
    df = io.load_results_df('performance_summary')

    # 1) Group level
    # Trials count
    vp.plot_trial_differences(df, save=save, show=show)

    # Plot accuracy and reaction time (both mean and median)
    for feature in [
        'acc', 'rt_mean', 'rt_med',
    ]:
        vp.plot_feature_overview(df, feature_col=feature, plot_style='violin', save=save, show=show)
        vp.plot_feature_overview(df, feature_col=feature, plot_style='box-outliers', save=save, show=show)
        vp.plot_feature_overview(df, feature_col=feature, plot_style='box-no_outliers', save=save, show=show)
        vp.plot_distribution_overview(df, feature_col=feature, save=save, show=show)

        # 2) Participant level
        vp.plot_each_sid_distribution_overview(df, feature_col=feature, save=save, show=show)


if __name__ == '__main__':
    run_data_overview_plots(
        show=False,
        save=True,
    )
