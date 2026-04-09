import pandas as pd
import numpy as np
from pandas.api.types import is_numeric_dtype


def s_to_ms(s_series: pd.Series) -> pd.Series:
    """
    Convert a numeric Series from seconds to milliseconds (rounded).
    :param s_series: Series in seconds.
    :return: Series in milliseconds.
    """
    if is_numeric_dtype(s_series):
        return s_series.apply(lambda val: np.round(val * 1000))
    raise TypeError(f'pd.Series {s_series} should be of numeric type!')


def mask_in_bounds_rows(
        col: pd.Series,
        n_std_top: float,
        bottom_bound: int = 200,
        top_use_median: bool = False
) -> pd.Series:
    """
    Return a boolean mask for rows within RT bounds.
    Top bound is defined as central_tendency + std_top * std; lower bound is fixed at bottom_bound.
    :param col: Series of reaction times in milliseconds.
    :param n_std_top: Number of standard deviations above the mean to use as top bound.
    :param bottom_bound: Minimum RT in milliseconds (default: 200ms).
    :param top_use_median: If True, use median instead of mean for the top bound (default: False).
    :return: Boolean Series, True where RT is within bounds.
    """
    center = col.median() if top_use_median else col.mean()
    top_bound = center + n_std_top * col.std()
    return (bottom_bound <= col) & (col < top_bound)
