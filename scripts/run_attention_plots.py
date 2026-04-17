import pandas as pd
import amber_utils.io_utils as io
from amber.viz.attention_viz import plot_iter_interv_effects


def run_all_interv_effects_plots(show: bool, test: bool, save: bool = False):
    """
    Run functions for plotting intervention effects over time for all groups and aggregation metrics.
    :return: None
    """
    df = pd.read_csv(io.get_tables_path() / 'attention_features.csv', index_col=0)
    for agg_metric, sub_df in df.groupby('att_rt_agg'):

        # By group
        plot_iter_interv_effects(sub_df, grouping_cols=['group'], att_rt_agg=str(agg_metric), show=show, test=test, save=save)

        # By amblyopia type and group
        plot_iter_interv_effects(sub_df, grouping_cols=['group', 'amb_type'], att_rt_agg=str(agg_metric), show=show, test=test, save=save)

        # By subject
        plot_iter_interv_effects(sub_df, grouping_cols=['sid'], att_rt_agg=str(agg_metric), show=show, test=test, save=save)


if __name__ == '__main__':
    run_all_interv_effects_plots(
        show=False,
        test=False,
        save=True,
    )
