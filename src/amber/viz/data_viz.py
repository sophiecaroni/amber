import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import amber_utils.viz_utils as vutils
import amber_utils.io_utils as io
from typing import Any
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from amber_utils.viz_utils import plot_context
from pathlib import Path
from copy import copy


def plot_feature_xcats(
        df: pd.DataFrame,
        feature_col: str,
        xcats_col: str | None = 'group',
        hue: str = 'Cueing',
        ax: Axes | None = None,
        plot_style='violin',
        split_violin: bool = True,
        **plot_kwargs: dict[str, Any],
) -> Figure:
    with plot_context():
        if ax is None:
            fig, ax = plt.subplots(figsize=(5, 3))
        else:
            fig = ax.figure

        plot_kwargs.update(
            dict(data=df, y=feature_col, hue=hue, palette=vutils.get_hue_palette(hue), ax=ax)
        )
        if xcats_col is not None:
            plot_kwargs.update(dict(x=xcats_col))
        if plot_style == 'violin':
            plot_kwargs.update(dict(split=split_violin))
            sns.violinplot(**plot_kwargs, cut=0, linewidth=0.5)
        elif plot_style == 'box-outliers':
            sns.boxplot(**plot_kwargs, showfliers=True)
        elif plot_style == 'scatter':
            np.random.seed(42)  # set seed for reproducibility of the stripplot jitter
            # Add different alphas for scatter and violins
            s_kwargs = copy(plot_kwargs)
            v_kwargs = copy(plot_kwargs)
            if 'alpha' not in plot_kwargs.keys():
                s_kwargs.update(dict(alpha=0.7))
                v_kwargs.update(dict(alpha=0.4))
            sns.stripplot(**s_kwargs, jitter=0.2, dodge=True, edgecolor='gray', linewidth=0.5)
            sns.violinplot(**v_kwargs, cut=0, linewidth=0.5, inner='quart', legend=False)
        else:  # plot_style == 'box-no_outliers':
            sns.boxplot(**plot_kwargs, showfliers=False)
    return fig


def plot_distribution_supercats(
        df: pd.DataFrame,
        feature_col: str,
        bins: int = 35,
        supercats_col: str | None = 'group',
        ax: Axes | None = None,
        **kwargs,
) -> Figure:
    with plot_context():
        if ax is None:
            fig, ax = plt.subplots()
        else:
            fig = ax.figure

        if supercats_col is None:
            sns.histplot(data=df, x=feature_col, bins=bins, stat="count", ax=ax, **kwargs)
        else:
            for cat, cat_df in df.groupby(supercats_col):
                spec_kwargs = kwargs.copy()
                if 'color' not in kwargs.keys():
                    if supercats_col == 'group':
                        spec_kwargs['color'] = vutils.get_group_palette()[cat]
                sns.histplot(data=cat_df, x=feature_col, bins=bins, stat="count", alpha=0.45, ax=ax,
                             label=str(cat).title(), **spec_kwargs)
            if len(df[supercats_col].unique()) > 1:
                plt.legend()
    return fig


def compare_subplots(
        df: pd.DataFrame,
        plot_fun,
        subplots_col: str = 'filt_cond',
        save: bool = False,
        show: bool = False,
        save_dir: str | Path | None = None,
        **plot_fun_kwargs
) -> Figure:
    with plot_context():
        n_subplots = len(df[subplots_col].unique())
        fig, axes = plt.subplots(1, n_subplots, sharey=True, figsize=(3*n_subplots, 3))
        if n_subplots == 1:
            axes = [axes]

        for (subplot_cond, sub_df), ax in zip(df.groupby(subplots_col), axes):
            plot_fun(df=sub_df, ax=ax, **plot_fun_kwargs)
            ax.set_title(str(subplot_cond).title())

        if save:
            fname = f'plot_filt'
            if 'feature_col' in plot_fun_kwargs.keys():
                fname += f"_{plot_fun_kwargs['feature_col']}"
            if 'plot_style' in plot_fun_kwargs.keys():
                fname += f"_{plot_fun_kwargs['plot_style']}"
            elif 'distribution' in plot_fun.__name__:
                fname += "_distribution"
            else:
                fname += f"_{plot_fun.__name__.replace('plot_', '').replace('compare_', '').replace('differences', '')}"
            vutils.save_figure(save_dir=save_dir, fname=fname, fig=fig)
        if show:
            plt.show()
    return fig


def plot_trials_count(
        df: pd.DataFrame,
        group_col: str | None = 'group',
        ax: Axes | None = None,
) -> Figure:
    with plot_context():
        if ax is None:
            ax = plt.subplot()
            fig = None
        else:
            fig = ax.figure

        if group_col is None:
            ax.bar(['All'], [df['trials'].sum()])
        else:
            grouped_df = df.groupby([group_col], as_index=False).agg(trials=('trials', 'sum'))
            ax.bar(grouped_df[group_col], grouped_df['trials'])
            _, ymax = ax.get_ylim()
            ymin = grouped_df['trials'].min() * 0.9
            ax.set_ylim(ymin, ymax)

        if fig is None:
            ax.set_ylabel('Total Trials')
        else:
            fig.supylabel('Total Trials')
    return fig


def _save_subdir(group_col: str | None) -> str:
    return 'group' if group_col is not None else 'all'


def plot_trial_differences(df: pd.DataFrame, group_col: str | None = 'group', save_dir: str | None = None, **kwargs):
    save_dir = save_dir or _save_subdir(group_col)
    compare_subplots(df, plot_fun=plot_trials_count, group_col=group_col,
                     save_dir=save_dir, **kwargs)


def plot_feature_overview(df: pd.DataFrame, feature_col: str, group_col: str | None = 'group',
                          save_dir: str | None = None, **kwargs):
    save_dir = save_dir or _save_subdir(group_col)
    compare_subplots(df, plot_fun=plot_feature_xcats, feature_col=feature_col, xcats_col=group_col,
                     save_dir=save_dir, **kwargs)


def plot_distribution_overview(df: pd.DataFrame, feature_col: str, group_col: str | None = 'group',
                                save_dir: str | None = None, **kwargs):
    save_dir = save_dir or _save_subdir(group_col)
    compare_subplots(df, plot_fun=plot_distribution_supercats, feature_col=feature_col, supercats_col=group_col,
                     save_dir=save_dir, **kwargs)


def plot_each_sid_distribution_overview(
        df: pd.DataFrame,
        feature_col: str,
        save: bool = False,
        show: bool = False,
        **kwargs
) -> None:
    with plot_context():
        for sid, sid_df in df.groupby('sid'):
            group = io.get_group(sid)
            fig = compare_subplots(sid_df, plot_fun=plot_distribution_supercats, feature_col=feature_col,
                                   supercats_col=None, color=vutils.get_group_palette()[group], **kwargs)
            fig.suptitle(f'{str(sid)} ({group})')
            if save:
                vutils.save_figure(save_dir=sid, fname=f'hist_{feature_col}', fig=fig)
            if show:
                plt.show()
                