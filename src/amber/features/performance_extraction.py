import pandas as pd
from pathlib import Path
from amber_utils import io_utils as io
from amber_utils.comp_utils import mask_in_bounds_rows
from amber.features import add_session_metadata_to_df


def extract_performance_features(session_fpath: Path) -> pd.DataFrame | None:
    """
    Extract accuracy and RT performance features from a single session file.
    Aggregates trials under multiple RT filtering thresholds.
    :param session_fpath: Path to the raw session CSV file.
    :return: DataFrame of performance features with session metadata columns.
    """
    session_df = io.load_session_df(session_fpath)

    # Aggregate across trials of the session based on different filtering thresholds of RT
    rt_top_filters = [None, 3]
    agg_df = _filt_and_agg_session_df(session_df, rt_top_filters)

    # Add demographics and experimental information columns
    agg_df = add_session_metadata_to_df(agg_df, session_fpath)

    return agg_df


def _filt_and_agg_session_df(
        session_df: pd.DataFrame,
        top_filt_thresholds: list[float | None],
) -> pd.DataFrame:
    group_cols = ['CueType', 'Audio', 'Cueing']
    agg_dfs_different_filters = []
    for thresh in top_filt_thresholds:
        if thresh is None:

            # Don't filter; aggregate and append
            agg_dfs_different_filters.append(
                _summarize_session_trials(session_df, group_cols, opt_col_name='filt_cond', opt_col_val='unfilt')
            )
        else:
            # Filter df based on thresh as upper bound and default as bottom bound
            filt_df = session_df.loc[mask_in_bounds_rows(session_df['RT_ms'], thresh)]

            # Aggregate and append
            agg_dfs_different_filters.append(
                _summarize_session_trials(filt_df, group_cols, opt_col_name='filt_cond', opt_col_val=str(thresh))
            )
    return pd.concat(agg_dfs_different_filters, ignore_index=True)


def _summarize_session_trials(
        session_df: pd.DataFrame,
        group_cols: list[str],
        opt_col_name: str | None = None,
        opt_col_val: str | None = None
) -> pd.DataFrame:
    # Compute accuracy on all trials
    all_trials_grp = session_df.groupby(group_cols, as_index=False)
    acc_df = all_trials_grp.agg(
        trials=('CueType', 'count'),
        acc=('Accuracy', 'mean'),  # correct trials / total trials
    )
    acc_df['acc'] = (acc_df['acc'] * 100).round(3)

    # Compute RT on successful trials (ie where accuracy=1), so ignore trials where accuraacy = 0
    corr_trials_grp = session_df[session_df["Accuracy"] == 1].groupby(group_cols, as_index=False)
    rt_df = corr_trials_grp.agg(
        rt_mean=("RT_ms", "mean"),
        rt_med=("RT_ms", "median"),
    )

    # Bring dfs together (groups with 0 correct trials will get NaN RTs)
    out_df = acc_df.merge(rt_df, on=group_cols, how="left")

    # Add optional column
    if opt_col_name is not None:
        out_df[opt_col_name] = opt_col_val
    return out_df