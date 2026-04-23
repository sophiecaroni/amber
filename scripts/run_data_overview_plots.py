import amber_utils.io_utils as io
import amber.viz.data_viz as vp
import numpy as np


def run_data_overview_plots(show: bool, save: bool = False):
    df = io.load_df('performance_summary')

    # Plot trials count, over all subjects or by group (superimposed)
    for group_col in [None, 'group']:
        vp.plot_trial_differences(df, group_col=group_col, save=save, show=show)

    # Plot accuracy and reaction time features...
    features = [
        'acc', 'rt_mean', 'rt_med',
    ]
    for feature in features:
        for group_col in [None, 'group']:

            # ... 1) distribution, over all subjects or by group (superimposed)
            for plot_style in [
                'violin', 'box-outliers', 'box-no_outliers', 'scatter'
            ]:
                vp.plot_feature_overview(df, feature_col=feature, group_col=group_col, plot_style=plot_style,
                                         save=save, show=show)

            # ... 2) trials count, over all subjects or by group (superimposed)
            vp.plot_distribution_overview(df, feature_col=feature, group_col=group_col, save=save, show=show)

        # ... 3) distribution, by subject (separately)
        vp.plot_each_sid_distribution_overview(df, feature_col=feature, save=save, show=show)


if __name__ == '__main__':
    run_data_overview_plots(
        show=False,
        save=True,
    )
