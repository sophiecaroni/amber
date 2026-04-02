import pandas as pd
import numpy as np
from typing import Callable


def compute_att_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute RT-based attention features for a single session. Features are computed using both mean and median RT
    aggregation.
    :param df: Filtered trials DataFrame for a session.
    :return: DataFrame with columns [att_type, att_rt_agg, att_val].
    """
    att_dfs = []
    for agg_fn in [np.mean, np.median]:

        # Compute cueing effects
        cueing_effects = compute_cueing_effects(df, agg_fn)

        # Compute attention features
        vis_sel_att = compute_vis_sel_att(**cueing_effects)
        audio_vis_att = compute_audio_vis_att(**cueing_effects)
        spat_att = compute_spat_att(trials_df=df)

        # Store attention features types, aggregation method and values in a df
        att_dfs.append(pd.DataFrame({
            'att_type': ['vis_sel', 'audio_vis', 'spat'],
            'att_rt_agg': agg_fn.__name__.replace('np.', ''),
            'att_val': [vis_sel_att, audio_vis_att, spat_att],
        }))

    # Concatenate dfs across aggregation methods
    return pd.concat(att_dfs, ignore_index=True)


def compute_cueing_effects(df: pd.DataFrame, agg_fn: Callable) -> dict:
    """
    Compute all four intermediate RT cueing effects (TCC/NCC x V/AV).
    :param df: Filtered trials DataFrame for a session.
    :param agg_fn: Aggregation function to apply to RT (e.g. np.mean or np.median).
    :return: Dict of cueing effect values keyed by condition name.
    """
    return dict(
        tcc_v=compute_tcc_visual_effect(df, agg_fn),
        ncc_v=compute_ncc_visual_effect(df, agg_fn),
        tcc_av=compute_tcc_audiovisual_effect(df, agg_fn),
        ncc_av=compute_ncc_audiovisual_effect(df, agg_fn),
    )


def compute_tcc_visual_effect(trials_df: pd.DataFrame, agg_fn: Callable) -> float:
    """
    Compute the spatial cueing effect for target-color cue (TCC) distractors in visual (V) trials.
    TCC distractors match the target color and capture top-down, goal-driven attention.
    :param trials_df: Trials DataFrame for a session.
    :param agg_fn: Aggregation function to apply to RT (e.g. np.mean or np.median).
    :return: Difference in aggregated RT between spatially invalid and valid cue trials.
    """
    tcc_v_df = trials_df[
        (trials_df['Audio'] == 'V') &
        (trials_df['CueType'] == 'tcc')
        ]
    rinval_rt = tcc_v_df.loc[tcc_v_df['Cueing'] == 'rinval', 'RT_ms']
    rval_rt = tcc_v_df.loc[tcc_v_df['Cueing'] == 'rval', 'RT_ms']

    return agg_fn(rinval_rt) - agg_fn(rval_rt)  # agg_fn operations are applied across rows (trials)


def compute_ncc_visual_effect(trials_df: pd.DataFrame, agg_fn: Callable) -> float:
    """
    Compute the spatial cueing effect for non-target-color cue (NCC) distractors in visual (V) trials.
    NCC distractors do not match the target color and serve as a baseline condition.
    :param trials_df: Trials DataFrame for a session.
    :param agg_fn: Aggregation function to apply to RT (e.g. np.mean or np.median).
    :return: Difference in aggregated RT between spatially invalid and valid cue trials.
    """
    ncc_v_df = trials_df[
        (trials_df['Audio'] == 'V') &
        (trials_df['CueType'] == 'ncc')
        ]
    rinval_rt = ncc_v_df.loc[ncc_v_df['Cueing'] == 'rinval', 'RT_ms']
    rval_rt = ncc_v_df.loc[ncc_v_df['Cueing'] == 'rval', 'RT_ms']

    return agg_fn(rinval_rt) - agg_fn(rval_rt)  # agg_fn operations are applied across rows (trials)


def compute_tcc_audiovisual_effect(trials_df: pd.DataFrame, agg_fn: Callable) -> float:
    """
    Compute the spatial cueing effect for target-color cue (TCC) distractors in audiovisual (AV) trials.
    AV trials include a spatially diffuse tone paired with the visual distractor.
    :param trials_df: Trials DataFrame for a session.
    :param agg_fn: Aggregation function to apply to RT (e.g. np.mean or np.median).
    :return: Difference in aggregated RT between spatially invalid and valid cue trials.
    """
    tcc_av_df = trials_df[
        (trials_df['Audio'] == 'AV') &
        (trials_df['CueType'] == 'tcc')
        ]
    rinval_rt = tcc_av_df.loc[tcc_av_df['Cueing'] == 'rinval', 'RT_ms']
    rval_rt = tcc_av_df.loc[tcc_av_df['Cueing'] == 'rval', 'RT_ms']

    return agg_fn(rinval_rt) - agg_fn(rval_rt)  # agg_fn operations are applied across rows (trials)


def compute_ncc_audiovisual_effect(trials_df: pd.DataFrame, agg_fn: Callable) -> float:
    """
    Compute the spatial cueing effect for non-target-color cue (NCC) distractors in audiovisual (AV) trials.
    AV trials include a spatially diffuse tone paired with the visual distractor.
    :param trials_df: Trials DataFrame for a session.
    :param agg_fn: Aggregation function to apply to RT (e.g. np.mean or np.median).
    :return: Difference in aggregated RT between spatially invalid and valid cue trials.
    """
    ncc_av_df = trials_df[
        (trials_df['Audio'] == 'AV') &
        (trials_df['CueType'] == 'ncc')
        ]
    rinval_rt = ncc_av_df.loc[ncc_av_df['Cueing'] == 'rinval', 'RT_ms']
    rval_rt = ncc_av_df.loc[ncc_av_df['Cueing'] == 'rval', 'RT_ms']

    return agg_fn(rinval_rt) - agg_fn(rval_rt)  # agg_fn operations are applied across rows (trials)


def compute_vis_sel_att(tcc_v: float, ncc_v: float, tcc_av: float, ncc_av: float) -> float:
    """
    Compute the visual selective attention score as the difference in cueing effects between target-color (TCC) and
    non-target-color (NCC) distractors, averaged across visual and audiovisual modalities.
    :param tcc_v: TCC cueing effect in visual trials.
    :param ncc_v: NCC cueing effect in visual trials.
    :param tcc_av: TCC cueing effect in audiovisual trials.
    :param ncc_av: NCC cueing effect in audiovisual trials.
    :return: Visual selective attention score.
    """
    return np.mean([tcc_v, tcc_av]) - np.mean([ncc_v, ncc_av])


def compute_audio_vis_att(tcc_v: float, ncc_v: float, tcc_av: float, ncc_av: float) -> float:
    """
    Compute the audiovisual attention score as the difference in cueing effects between visual and audiovisual
    distractors, averaged across target-color (TCC) and non-target-color (NCC) cue types.
    :param tcc_v: TCC cueing effect in visual trials.
    :param ncc_v: NCC cueing effect in visual trials.
    :param tcc_av: TCC cueing effect in audiovisual trials.
    :param ncc_av: NCC cueing effect in audiovisual trials.
    :return: Audiovisual attention score.
    """
    return np.mean([tcc_v, ncc_v]) - np.mean([tcc_av, ncc_av])


def compute_spat_att(trials_df: pd.DataFrame) -> float:
    """
    Compute the spatial attention score as the overall RT cueing effect across all trials.
    :param trials_df: Trials DataFrame for a session.
    :return: Difference in mean RT between spatially invalid and valid cue trials.
    """
    rinval_rt = trials_df.loc[trials_df['Cueing'] == 'rinval', 'RT_ms']
    rval_rt = trials_df.loc[trials_df['Cueing'] == 'rval', 'RT_ms']
    return rinval_rt.mean() - rval_rt.mean()