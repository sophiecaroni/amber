import pandas as pd
import re
from amber.features import add_session_metadata_to_df
from amber_utils.io_utils import get_data_path


def _format_acq_df(df_label: str, df: pd.DataFrame) -> pd.DataFrame:
    """Formats df of vision acquity data."""
    df = df.copy()
    parts = df_label.split('_')
    if len(parts) != 3:
        raise ValueError('Unexpected format of acq sheet name!')
    df['vis_type'] = 'acq'
    df['vis_test'] = parts[1].lower()[:3]  # only encode via three first letters
    df['eye_cond'] = 'ND' if parts[2].lower().startswith('am') else 'DO'
    return df


def _format_stereo_df(df_label: str, df: pd.DataFrame) -> pd.DataFrame:
    """Formats df of stereovision data."""
    df = df.copy()
    parts = df_label.split('_')
    if len(parts) != 2:
        raise ValueError('Unexpected format of acq sheet name!')
    df['vis_type'] = 'ste'
    df['vis_test'] = parts[1].lower()[:3]  # only encode via three first letters

    # Stereovision tests are conducted on both eyes, so duplicate current df for each eye condition
    df_do = df.copy()
    df_do['eye_cond'] = 'DO'
    df_nd = df.copy()
    df_nd['eye_cond'] = 'ND'
    final_df = pd.concat([df_do, df_nd], ignore_index=True)
    return final_df


def _format_vision_df(df_label: str, df: pd.DataFrame) -> pd.DataFrame:
    """Formats dataframe of vision data."""
    df = df.copy()

    # Format existing columns and handle nans
    old_sid_col = 'Old AMB code'
    df.dropna(subset=[old_sid_col], how='all', inplace=True)
    df['sid'] = df[old_sid_col].apply(lambda val: re.search(r'AMB\d\d', val))
    df.dropna(subset='sid', inplace=True)  # Drop rows where sid is nan or None (no match found)
    df['sid'] = df['sid'].apply(lambda val: val.group(0))  # ungroup valid matches
    df.drop(columns=[old_sid_col, 'New code'], inplace=True)  # useless cols

    # Transform to long format
    df = df.melt(id_vars=['sid'], var_name='cond', value_name='vis_score')
    df.dropna(subset=['vis_score'], axis=0, inplace=True)  # drop rows missing a vis_score value (it means the participant was not measured there

    # Split "cond" values into interv_eff and interv
    split = df['cond'].str.extract(r'^(?P<interv_eff>.+)[-_](?P<interv>VR|OA)$')
    df = pd.concat([df.drop(columns='cond'), split], axis=1)

    # Format interv_eff values
    df.replace({'interv_eff': {'Screen': 'BL', 'Post': 'ST', 'F-up': 'FU'}}, inplace=True)

    if df_label.startswith('BCVA'):
        df = _format_acq_df(df_label, df)
    else:
        df = _format_stereo_df(df_label, df)

    df = add_session_metadata_to_df(df)
    return df.reset_index(drop=True)


def extract_vision_features() -> pd.DataFrame:
    all_sheets = pd.read_excel(get_data_path()/ "extra" / "20260616_AMBER_BCVA&STEREOdata.xlsx", sheet_name=None)
    for name, sheet in all_sheets.items():
        all_sheets[name] = _format_vision_df(name, sheet)

    final_df = pd.concat(all_sheets.values()).sort_values(by=['sid', 'interv', 'interv_eff', 'vis_type', 'vis_test'])
    return final_df.reset_index(drop=True)
