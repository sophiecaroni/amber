import re
import numpy as np
import warnings
from pathlib import Path


def get_session_sid(session_fpath: Path) -> str | None:
    """
    Extract the subject ID (e.g. 'AMB01') of a session from its file path.
    :param session_fpath: Path to the session file.
    :return: Subject ID string, or raises ValueError if not found.
    """
    fname = session_fpath.stem  # get file name without extension

    match = re.search(r"(?i)(?:^|_)AMB_?\d{2}(?:_|$)", fname)
    if match:
        # extract just the ID (strip surrounding underscores if they were matched)
        sid = re.search(r"(?i)AMB_?\d{2}", match.group(0)).group(0)
        return sid

    # If no sid is found in file name, print warning and return None
    raise ValueError(f"AMB-sid not found in this file name! {fname}")


def get_session_eye_cond(session_fpath: Path) -> str | None:
    """
    Extract the eye condition ('DO' or 'ND') of a session from its file path.
    :param session_fpath: Path to the session file.
    :return: Eye condition string, or None with a warning if not found.
    """
    fpath_str = str(session_fpath)
    path_parts = np.array([i.lower() for i in fpath_str.split('_')])

    # Discard directories, focus on file name
    fname_parts = path_parts[1:]

    conds = np.array(['do', 'nd'])
    cond_idx = np.where(np.isin(fname_parts, conds))[0]

    # Extract condition (even if there are multiple conditions, just take the first one)
    if len(cond_idx) > 0:
        cond_idx = cond_idx[0]
        cond = fname_parts[int(cond_idx)]
        return str(cond).upper()

    # If no condition is found, try to find a non-underscore form (e.g. T4ND)
    embedded = [p for p in fname_parts if re.fullmatch(r"t\d{1,2}(do|nd)", p)]
    if embedded:
        m = re.fullmatch(r"t\d{1,2}(do|nd)", embedded[0])
        return m.group(1).upper()

    # If no eye condition is found in file name, print warning and return None
    warnings.warn(f'Eye-condition not found in this file name! {session_fpath.stem}', UserWarning)
    return None


def get_session_tpoint(session_fpath: Path) -> str | None:
    """
    Extract the timepoint ('T1' - 'T5') of a session from its file path.
    :param session_fpath: Path to the session file.
    :return: Timepoint string, or None with a warning if not found.
    """
    fpath_str = str(session_fpath)
    path_parts = np.array([i.lower() for i in fpath_str.split('_')])

    # Discard directories, focus on file name
    fname_parts = path_parts[1:]

    pattern = re.compile('_?t*[1-5]$')
    tpoint_lst = list(filter(pattern.match, fname_parts))

    if tpoint_lst:
        # Take first element of the list (even if more timepoints are found)
        tpoint = tpoint_lst[0]
        return tpoint.upper()

    # If no timepoint is found in file name, print warning and return None
    warnings.warn(f'Time-point not found in this file name! {session_fpath.stem}', UserWarning)
    return None
