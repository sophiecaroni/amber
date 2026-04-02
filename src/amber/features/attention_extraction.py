import pandas as pd
from pathlib import Path
from amber_utils import io_utils as io, comp_utils as cu
from amber.features import add_session_metadata_to_df
from amber.features.attention import compute_att_features


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