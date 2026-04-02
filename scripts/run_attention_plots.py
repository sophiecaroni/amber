import pandas as pd
from viz.attention_viz import plot_iter_interv_effects


def run_all_interv_effects_plots(show: bool, save: bool = False):
    """
    Run functions for plotting intervention effects over time for all groups and aggregation metrics.
    :return: 
    """
    df = pd.read_csv('/Users/sophiecaroni/amber/outputs/results/attention_features.csv', index_col=0)
    for agg_metric, sub_df in df.groupby('att_rt_agg'):

        # By group
        plot_iter_interv_effects(sub_df, grouping_cols=['group'], att_rt_agg=str(agg_metric), show=show, save=save)

        # By amblyopia type and group
        plot_iter_interv_effects(sub_df, grouping_cols=['group', 'amb_type'], att_rt_agg=str(agg_metric), show=show, save=save)

        # By subject
        plot_iter_interv_effects(sub_df, grouping_cols=['sid'], att_rt_agg=str(agg_metric), show=show, save=save)


if __name__ == '__main__':
    run_all_interv_effects_plots(
        show=True,
        save=False,
    )
