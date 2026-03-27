import pandas as pd
import pytest
import amber_utils.comp_utils


def test_s_to_ms():
    inp_series = pd.Series(['a', 'b', 'c'])
    with pytest.raises(TypeError):
        amber_utils.comp_utils.s_to_ms(inp_series)


