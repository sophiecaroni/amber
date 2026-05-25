import amber_utils.io_utils as io
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from amber.viz.data_viz import compare_subplots, plot_feature_xcats
from amber_utils.io_utils import get_group
from amber_utils.viz_utils import get_interv_palette, save_figure, get_eye_cond_label, plot_context


def plot_lmm_predictions(metric: str, save: bool = False, show: bool = True):
    df_path = io.get_stats_path() / f'results_{metric}.csv'
    df = pd.read_csv(df_path)
    df['group'] = df['sid'].apply(get_group)

    hue = 'interv'
    grouping_cols = ['group', 'eye_cond']
    with plot_context():
        for conds, cond_df in df.groupby(grouping_cols):

            # Plot data distribution
            fig = compare_subplots(
                cond_df,
                plot_feature_xcats,
                feature_col=metric,
                xcats_col='interv_eff',
                subplots_col='group',
                hue=hue,
                plot_style='scatter',
                alpha=0.3,
                save=False,
                show=False,
            )

            # Plot model predictions on top of data
            sns.pointplot(
                data=cond_df,
                x='interv_eff',
                y='fitted',
                hue=hue,
                dodge=0.25,
                join=True,
                markers='d',
                scale=0.7,
                zorder=10,
                legend=False,
                palette=get_interv_palette(),
            )
            title = f'LMM predictions for {conds[0]}, {get_eye_cond_label(conds[1]).lower()}'
            fig.get_axes()[0].set_title(title)

            if show:
                plt.show()
            if save:
                save_figure(fig=fig, save_dir=io.get_figures_path() / 'LMM', fname=f'results_{metric}_{"_".join(list(conds))}.png')
            plt.close()

