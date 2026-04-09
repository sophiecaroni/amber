import pandas as pd
from pathlib import Path
from amber_utils import io_utils as io
from amber_utils.comp_utils import mask_in_bounds_rows
from amber.features import add_session_metadata_to_df

_GROUP_COLS = ['CueType', 'Audio', 'Cueing']


def extract_performance_features(session_fpath: Path) -> pd.DataFrame | None:
    """
    Extract accuracy and RT performance features from a single session file.
    Aggregates trials under multiple RT filtering thresholds.
    :param session_fpath: Path to the raw session CSV file.
    :return: DataFrame of performance features with session metadata columns.
    """
    session_df = io.load_session_df(session_fpath)

    # Aggregate using mean-based and median-based RT filtering, separately
    rt_top_filters = [None, 3]
    mean_agg_df = _filt_and_agg_session_df(session_df, rt_top_filters, use_median=False)  # RT is in column 'rt_mean'
    med_agg_df = _filt_and_agg_session_df(session_df, rt_top_filters, use_median=True)  # RT is in column 'rt_med'

    # The two dfs are the same except for RT columns; so merge RT column from med_agg_df ('rt_med') into mean_agg_df
    merge_cols = _GROUP_COLS + ['filt_cond']
    agg_df = mean_agg_df.merge(med_agg_df[merge_cols + ['rt_med']], on=merge_cols, how='left')

    # Add demographics and experimental information columns
    agg_df = add_session_metadata_to_df(agg_df, session_fpath)

    return agg_df


def _filt_and_agg_session_df(
        session_df: pd.DataFrame,
        top_filt_thresholds: list[float | None],
        use_median: bool = False,
) -> pd.DataFrame:
    """
    Filter session trials by RT bounds and aggregate per group.
    :param session_df: Raw session DataFrame.
    :param top_filt_thresholds: List of upper-bound multipliers (in std units), or None for unfiltered.
    :param use_median: If True, use median-based upper bound for filtering.
    :return: Aggregated DataFrame with one row per group per filter condition.
    """
    agg_dfs = []
    for thresh in top_filt_thresholds:
        if thresh is None:

            # Don't filter; aggregate and append
            agg_dfs.append(
                _summarize_session_trials(session_df, _GROUP_COLS, opt_col_name='filt_cond', opt_col_val='unfilt', use_median=use_median)
            )
        else:
            # Filter df based on thresh as upper bound and default as bottom bound
            filt_df = session_df.loc[mask_in_bounds_rows(session_df['RT_ms'], thresh, top_use_median=use_median)]

            # Aggregate and append
            agg_dfs.append(
                _summarize_session_trials(filt_df, _GROUP_COLS, use_median=use_median, opt_col_name='filt_cond', opt_col_val=str(thresh))
            )
    return pd.concat(agg_dfs, ignore_index=True)


def _summarize_session_trials(
        session_df: pd.DataFrame,
        group_cols: list[str],
        use_median: bool = False,
        opt_col_name: str | None = None,
        opt_col_val: str | None = None
) -> pd.DataFrame:
    # Compute accuracy on all trials
    acc_df = session_df.groupby(group_cols, as_index=False).agg(
        trials=('CueType', 'count'),
        acc=('Accuracy', 'mean'),  # correct trials / total trials
    )
    acc_df['acc'] = (acc_df['acc'] * 100).round(3)

    # Compute RT on successful trials (ie where accuracy=1), so ignore trials where accuraacy = 0
    corr_df = session_df[session_df['Accuracy'] == 1].groupby(group_cols, as_index=False)
    if use_median:
        rt_df = corr_df.agg(rt_med=('RT_ms', 'median'))
    else:
        rt_df = corr_df.agg(rt_mean=('RT_ms', 'mean'))

    # Bring dfs together (groups with 0 correct trials will get NaN RTs)
    out_df = acc_df.merge(rt_df, on=group_cols, how='left')

    # Add optional column
    if opt_col_name is not None:
        out_df[opt_col_name] = opt_col_val
    return out_df