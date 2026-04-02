import pandas as pd
import matplotlib.pyplot as plt
import amber_utils.viz_utils as vutils
from viz.data_viz import plot_feature_xcats
from matplotlib.figure import Figure


def plot_interv_effects(
        df: pd.DataFrame,
        att_rt_agg: str = 'mean',
) -> Figure:
    # Filter by aggregating metric
    df = df.copy()
    if att_rt_agg not in df['att_rt_agg'].unique():
        raise ValueError(f'Value of att_rt_agg absent in df: {att_rt_agg=}')
    df = df[df['att_rt_agg'] == att_rt_agg]

    # Interventions are encoded as VR, OA, but also VR-OA and OA-VR
    intervs = {i for interv in df['interv'].unique() for i in interv.split('-')}
    n_interv = len(intervs)
    fig, axs = plt.subplots(1, n_interv, sharey=True, figsize=(12, 6))
    if n_interv == 1:
        axs = [axs]

    for interv, ax in zip(intervs, axs):
        interv_df = df[df['interv'].str.contains(interv)]

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
        fig = plot_feature_xcats(
            interv_df,
            feature_col='att_val',
            xcats_col='Assessment',
            hue='att_type',
            # split_violin=False,
            plot_style='scatter',
            ax=ax,
        )

        # Axis customization
        interv_label = vutils.get_interv_label(interv)
        ax.set_title(interv_label)
        ax.set_ylabel(f'{att_rt_agg.title()} Score')
    return fig


def plot_iter_interv_effects(
        df: pd.DataFrame,
        grouping_cols: list[str],
        att_rt_agg: str = 'mean',
        show: bool = True,
        test: bool = False,
        save: bool = False,
) -> None:
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
