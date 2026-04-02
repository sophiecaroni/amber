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


def mask_in_bounds_rows(col: pd.Series, n_std_top: float, bottom_bound: int = 200) -> pd.Series:
    """
    Return a boolean mask for rows within RT bounds.
    Upper bound is defined as mean + std_top * std; lower bound is fixed at bottom_bound.
    :param col: Series of reaction times in milliseconds.
    :param n_std_top: Number of standard deviations above the mean to use as upper bound.
    :param bottom_bound: Minimum RT in milliseconds (default: 200ms).
    :return: Boolean Series, True where RT is within bounds.
    """
    top_bound = col.mean() + n_std_top * col.std()  # reaction time < rt_top_bound (i.e. < std_top*std)
    return (bottom_bound <= col) & (col < top_bound)
