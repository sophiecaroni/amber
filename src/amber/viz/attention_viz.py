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

        # Get unique intervention types
        intervs = {i for interv in df['interv'].unique() for i in interv.split('-')}  # interventions are encoded as VR, OA, but also VR-OA and OA-VR
        n_interv = len(intervs)

        # Get eye-conditions
        econds = df['eye_cond'].unique()
        n_econds = len(econds)

        # Create eye-conditions x intervention types figure
        fig, axs = plt.subplots(n_econds, n_interv, sharey=True, sharex=True, figsize=(6*n_interv, 5*n_econds))
        axs = np.array([axs]).reshape((n_econds, n_interv))  # make sure we have a 2D axs array

        # Plot one eye-condition per row and one intervention per column
        for (econd, econd_df), row_axs in zip(df.groupby('eye_cond'), axs):
            for interv, ax in zip(intervs, row_axs):
                interv_df = econd_df[econd_df['interv'].str.contains(interv)]

                def assign_assessment(row):
                    tpoint = row['tpoint']

                    # T3 is follow-up of the intervention before '-' and baseline of the intervention after '-' (e.g. if intervenvtion is 'VR-OA', VR is at the follow-up and OA at the baseline
                    if tpoint == 'T3':
                        first = row['interv'].split('-')[0]
                        if first == interv:
                            return 'Follow-up'
                        else:
                            return 'Baseline'
                    elif tpoint == 'T1':  # always baseline
                        return 'Baseline'
                    elif tpoint == 'T2' or tpoint == 'T4':  # always short-term
                        return 'Short-term'
                    elif tpoint == 'T5':
                        return 'Follow-up'  # always follow-up
                    else:
                        raise ValueError(f'Unknown tpoint value: {tpoint=}')

                # Define assessment column containing assigned 'Baseline' / 'Short-term' / 'Follow-up'
                interv_df['Assessment'] = interv_df.apply(assign_assessment, axis=1)

                # Sort so that plots always appear in the order  'Baseline' / 'Short-term' / 'Follow-up'
                order = ['Baseline', 'Short-term', 'Follow-up']
                interv_df['Assessment'] = pd.Categorical(interv_df['Assessment'], categories=order, ordered=True)
                interv_df.sort_values(['Assessment', 'att_type'], inplace=True)

                # Call plot
                plot_feature_xcats(
                    interv_df,
                    feature_col='att_val',
                    xcats_col='Assessment',
                    hue='att_type',
                    # split_violin=False,
                    plot_style='scatter',
                    ax=ax,
                )

                # Customize axis
                interv_label = vutils.get_interv_label(interv)
                econd_label = vutils.get_econd_label(econd)
                ax.set_title(f"{interv_label} - {econd_label}")
                ax.set_ylabel(f'{att_rt_agg.title()} Score')

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
