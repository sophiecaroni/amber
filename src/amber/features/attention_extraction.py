import numpy as np
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

    # Compute attention features across trials of the session, using mean RT for internal computations
    mean_filt_df = session_df.loc[cu.mask_in_bounds_rows(session_df['RT_ms'], top_thresh)]  # use mean-based filtering
    mean_filt_df = mean_filt_df[mean_filt_df['Accuracy'] == 1]  # Only consider successful trials

    # Compute attention features across trials of the session, using median RT for internal computations
    med_filt_df = session_df.loc[cu.mask_in_bounds_rows(session_df['RT_ms'], top_thresh, top_use_median=True)]  # use median-based filtering
    med_filt_df = med_filt_df[med_filt_df['Accuracy'] == 1]  # Only consider successful trials

    # Compute RT attention features across trials of the session
    session_att_df = pd.concat([
        compute_att_features(mean_filt_df, np.mean),
        compute_att_features(med_filt_df, np.median),
    ], ignore_index=True)

    # Add demographics and experimental information columns
    session_att_df = add_session_metadata_to_df(session_att_df, session_fpath)

    return session_att_df
