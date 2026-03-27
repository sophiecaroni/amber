import pandas as pd
import amber_utils.parsing_utils as prs
from pathlib import Path
from amber_utils import io_utils as io, comp_utils as cu
from amber_utils.comp_utils import mask_in_bounds_rows
from src.amber.attention_computations import compute_att_features


def extract_attention_features(session_fpath: Path) -> pd.DataFrame | None:
    """
    Extract RT-based attention features from a single session file.
    Filters trials by RT bounds and accuracy before computing attention features.
    :param session_fpath: Path to the raw session CSV file.
    :return: DataFrame of attention features with session metadata columns.
    """
    session_df = io.load_session_df(session_fpath)

    # Filter qualifying trials
    top_thresh = 3.0
    filt_df = session_df.loc[cu.mask_in_bounds_rows(session_df['RT_ms'], top_thresh)]

    # Only consider successful trials
    filt_df = filt_df[filt_df['Accuracy'] == 1]

    # Add demographics and experimental conditions as columns
    add_session_metadata_to_df(filt_df, session_fpath)

    # Compute RT attention features across trials of the session
    session_att_df = compute_att_features(filt_df)

    # Add demographics and experimental information columns
    add_session_metadata_to_df(session_att_df, session_fpath)

    return session_att_df


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
    add_session_metadata_to_df(agg_df, session_fpath)

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


def add_session_metadata_to_df(df: pd.DataFrame, session_fpath: Path) -> None:
    sid = prs.get_sid_from_session_fpath(session_fpath)
    df.insert(0, 'sid', sid)
    df.insert(1, 'amb_type', io.get_amb_type(sid))
    df.insert(2, 'age', io.get_age(sid))
    df.insert(3, 'group', io.get_group(sid))
    df.insert(4, 'eye_cond', prs.get_eye_cond_from_session_fpath(session_fpath))
    tpoint = prs.get_tpoint_from_session_fpath(session_fpath)
    df.insert(5, 'tpoint', tpoint)
    df.insert(6, 'interv', io.get_sid_interv(sid, tpoint))


def extract_all_sessions(extract_fn, test: bool):
    """
    Run an extraction function over all raw session files and concatenate results.
    :param extract_fn: Extraction function to apply to each session file (e.g. extract_attention_features).
    :param test: If True, only process the first session file.
    :return: Concatenated DataFrame of results across all sessions.
    """
    raw_session_files = io.get_raw_session_fnames()
    all_dfs = []
    if test:
        raw_session_files = raw_session_files[:1]

    for session_fpath in raw_session_files:
        session_fpath = Path(session_fpath)
        df = extract_fn(session_fpath)
        print(f"\nFinished processing: {session_fpath}")
        all_dfs.append(df)

    if not all_dfs:
        raise ValueError("No session tables were extracted.")

    return pd.concat(all_dfs, ignore_index=True)
