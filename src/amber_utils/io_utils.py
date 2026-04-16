import pandas as pd
import os
from pathlib import Path
from glob import glob
from os.path import join
from amber_utils.comp_utils import s_to_ms


def set_for_save(path: Path) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_project_path() -> Path:
    return Path(__file__).resolve().parent.parent


def get_data_path() -> Path:
    return get_project_path() / 'data'


def get_raw_data_path() -> Path:
    return set_for_save(get_data_path() / 'raw')


def get_tables_path() -> Path:
    return set_for_save(get_outputs_path() / 'tables')


def get_figures_path() -> Path:
    return set_for_save(get_outputs_path() / 'figures')


def get_outputs_path(sid: str | None = None) -> Path:
    outputs_path = get_project_path() / 'outputs'

    if sid is None:
        return outputs_path

    outputs_path /= sid

    return set_for_save(outputs_path)


def load_rec_metadata_df(fpath: str | Path | None = None) -> pd.DataFrame:
    fpath = fpath or f'{get_data_path()}/extra'
    df = pd.read_excel(f'{fpath}/AMBER_rec_metadata.xlsx', index_col=0)

    # Clean up subject IDs index column
    df.index = [sid[:5] for sid in df.index]

    return df


def get_amb_type(sid) -> str:
    age_table = load_rec_metadata_df()
    return str(age_table.loc[sid, 'amb_type']).lower()


def get_age(sid) -> int:
    age_table = load_rec_metadata_df()
    return age_table.loc[sid, 'age'].astype(int)


def get_group(sid) -> str:
    age_table = load_rec_metadata_df()
    age = age_table.loc[sid, 'age'].astype(int)
    return 'adults' if age >= 18 else 'children'


def get_second_interv(first_interv: str) -> str | None:
    if first_interv.startswith('VR'):
        return 'OA'
    elif first_interv.startswith('OA'):
        return 'VR'
    else:
        return None


def get_sid_interv_pair(sid: str) -> tuple[str, str]:
    interv_table = load_rec_metadata_df()
    first_interv = interv_table.loc[sid, 'first_interv']
    second_interv = get_second_interv(first_interv)
    return first_interv, second_interv


def get_sid_interv(sid: str, tpoint: str) -> str:
    first_interv, second_interv = get_sid_interv_pair(sid)
    if tpoint.endswith('1') or tpoint.endswith('2'):
        return first_interv
    elif tpoint.endswith('4') or tpoint.endswith('5'):
        return second_interv
    elif tpoint.endswith('3'):
        return f"{first_interv}-{second_interv}"
    else:
        raise ValueError(f'Invalid tpoint {tpoint}')


def load_df(fname, sid: str | None = None) -> pd.DataFrame:
    fpath = get_tables_path()
    if sid:
        fpath /= sid
    fpath /= f'{fname}.csv'
    return pd.read_csv(fpath, index_col=0)


def get_raw_session_fnames():
    return sorted(glob(join(get_raw_data_path(), 'MSDA_AMB*.txt')))


def load_session_df(session_fpath: Path) -> pd.DataFrame:
    if session_fpath.suffix != '.txt':
        raise ValueError(f'Expected session txt format, got {session_fpath}')
    if not os.path.exists(session_fpath):
        raise FileNotFoundError(f'Session txt file {session_fpath.stem} not found at {session_fpath.parent}')
    session_df = pd.read_csv(session_fpath, sep=",", header=7)

    # Convert reaction time from s into ms
    session_df['RT_ms'] = s_to_ms(session_df['ReactionTime'])

    # Missed trials are denoted with Accuracy = -1; consider them as wrong trials (Accuracy = 0)
    session_df['Accuracy'] = session_df['Accuracy'].replace(-1, 0)
    return session_df






