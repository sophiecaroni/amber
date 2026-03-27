import pytest
import amber_utils.parsing_utils as prs
from pathlib import Path


@pytest.mark.parametrize(
    'inp, expected', [
        (Path('MSDA_AMB06_T1_DO_Blue_Hor_FirstND_T1_AMB_29-3-2023'), 'T1'),
    ]
)
def test_get_tpoint_from_session_fpath(inp, expected):
    assert prs.get_tpoint_from_session_fpath(inp) == expected


@pytest.mark.parametrize(
    'inp, expected', [
        (Path('MSDA_AMB16_T1_DO_Blue_Vert_SecondD_T1_AMB_18-4-2023'), 'DO'),
        (Path('MSDA_AMB14_T2_DO_Blue_Hor_SecondND_T1_AMB_27-6-2023'), 'DO')
    ]
)
def test_get_eye_cond_from_session_fpath(inp, expected):
    assert prs.get_eye_cond_from_session_fpath(inp) == expected


def test_get_sid_from_session_fpath_raises_error():
    fpath = Path("session_file_without_sid.txt")
    with pytest.raises(ValueError):
        prs.get_sid_from_session_fpath(fpath)
