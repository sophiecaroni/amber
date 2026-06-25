import pandas as pd
import amber_utils.parsing_utils as prs
from typing import Callable
from pathlib import Path
from amber_utils import io_utils as io


def _add_metadata_from_session_file(df: pd.DataFrame, session_fpath: Path) -> pd.DataFrame:
    df = df.copy()
    sid = prs.get_session_sid(session_fpath)
    df.insert(0, 'sid', sid)
    df.insert(1, 'amb_type', io.get_amb_type(sid))
    df.insert(2, 'age', io.get_age(sid))
    df.insert(3, 'group', io.get_group(sid))
    df.insert(4, 'eye_cond', prs.get_session_eye_cond(session_fpath))
    tpoint = prs.get_session_tpoint(session_fpath)
    df.insert(5, 'tpoint', tpoint)
    if tpoint.endswith('3'):
        first_interv, second_interv = io.get_sid_interv_pair(sid)
        df.insert(6, 'interv', first_interv)
        df.insert(7, 'interv_eff', 'FU')
        df2 = df.copy()
        df2['interv'] = second_interv
        df2['interv_eff'] = 'BL'
        return pd.concat([df, df2], ignore_index=True)
    else:
        df.insert(6, 'interv', io.get_sid_interv(sid, tpoint))
        df.insert(7, 'interv_eff', prs.get_tpoint_interv_eff(tpoint))
        return df


def _add_metadata_from_vis_df(vis_df: pd.DataFrame) -> pd.DataFrame:
    if 'sid' not in vis_df.columns:
        raise ValueError("Need 'sid' column to extract metadata.")
    sid_dfs_w_meta = []
    for sid, sid_df in vis_df.groupby('sid'):
        sid_df.insert(1, 'amb_type', io.get_amb_type(sid))
        sid_df.insert(2, 'age', io.get_age(sid))
        sid_df.insert(3, 'group', io.get_group(sid))
        sid_dfs_w_meta.append(sid_df)
    vis_df_w_meta = pd.concat(sid_dfs_w_meta, ignore_index=True)
    return vis_df_w_meta


def add_session_metadata_to_df(df: pd.DataFrame, session_fpath: Path | None = None) -> pd.DataFrame:
    if session_fpath is not None:
        return _add_metadata_from_session_file(df, session_fpath)
    else:
        return _add_metadata_from_vis_df(df)


def extract_all_sessions(extract_fn: Callable, test: bool):
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

