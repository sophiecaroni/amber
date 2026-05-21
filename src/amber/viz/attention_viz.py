import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import amber_utils.viz_utils as vutils
from amber.viz.data_viz import plot_feature_xcats
from matplotlib.figure import Figure


def plot_interv_effects(
        df: pd.DataFrame,
        att_rt_agg: str = 'mean',
) -> Figure:
    """
    Cereates a subplots figure for intervention effects on attentional features.
    Organize eye-conditions (dominant vs. non-dominant) on rows, intervention type (VR. vs glasses) on columns,
    assesment window (baseline vs. short-term vs. follow-up) on x-axis, attention score on y-axis and attention type for hue.
    :param df:
    :param att_rt_agg:
    :return:
    """
    with vutils.plot_context():
        # Filter by aggregating metric
        df = df.copy()
        if att_rt_agg not in df['att_rt_agg'].unique():
            raise ValueError(f'Value of att_rt_agg absent in df: {att_rt_agg=}')
        df = df[df['att_rt_agg'] == att_rt_agg]

        # Get unique intervention types and eye-conditions
        intervs = df['interv'].unique()
        n_interv = len(intervs)
        econds = df['eye_cond'].unique()
        n_econds = len(econds)

        # Create eye-conditions x intervention types figure
        fig, axs = plt.subplots(n_econds, n_interv, sharey=True, sharex=True, figsize=(6*n_interv, 5*n_econds))
        axs = np.array([axs]).reshape((n_econds, n_interv))  # make sure we have a 2D axs array

        # Plot one eye-condition per row and one intervention per column
        for (econd, econd_df), row_axs in zip(df.groupby('eye_cond'), axs):
            for interv, ax in zip(intervs, row_axs):
                interv_df = econd_df[econd_df['interv'] == interv].copy()

                # Sort interv_eff to arbotrary order and map to display labels
                order = ['BL', 'ST', 'FU']
                interv_df['interv_eff'] = pd.Categorical(interv_df['interv_eff'], categories=order, ordered=True)
                interv_df.sort_values(['interv_eff', 'att_type'], inplace=True)
                interv_df['interv_eff'] = interv_df['interv_eff'].map(vutils.get_interv_eff_label)

                # Call plot
                plot_feature_xcats(
                    interv_df,
                    feature_col='att_val',
                    xcats_col='interv_eff',
                    hue='att_type',
                    # split_violin=False,
                    plot_style='scatter',
                    ax=ax,
                )

                # Customize axis
                interv_label = vutils.get_interv_label(interv)
                econd_label = vutils.get_eye_cond_label(econd)
                ax.set_title(f"{interv_label} - {econd_label}")
                ax.set_ylabel(f'{att_rt_agg.title()} Score')
                ax.set_xlabel('Intervention Effect')

                # Customize legend
                handles, labels = ax.get_legend_handles_labels()
                ax.legend(handles, [vutils.get_att_type_label(l) for l in labels], title='Attention type')

        return fig


def plot_iter_interv_effects(
        df: pd.DataFrame,
        grouping_cols: list[str],
        att_rt_agg: str = 'mean',
        show: bool = True,
        test: bool = False,
        save: bool = False,
) -> None:
    with vutils.plot_context():
        figs = []
        for grouping_vals, grouped_df in df.groupby(grouping_cols):
            fig = plot_interv_effects(grouped_df, att_rt_agg)
            grouping_vals = list(grouping_vals)
            fig.suptitle(' '.join(grouping_vals).title())
            if save:
                fname = f'plot_interv_effects_{'_'.join(grouping_vals)}_{att_rt_agg}.png'
                save_dir = grouping_vals[0] if grouping_cols == ['sid'] else None
                vutils.save_figure(fname=fname, fig=fig, save_dir=save_dir)
            if show:
                fig.show()
            else:
                plt.close(fig=fig)
            figs.append(fig)
            if figs and test:
                break
