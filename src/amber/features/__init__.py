import pandas as pd
import amber_utils.parsing_utils as prs
from pathlib import Path
from amber_utils import io_utils as io


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