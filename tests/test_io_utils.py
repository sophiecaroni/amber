import amber_utils.io_utils as io
import pandas as pd
import pytest
from unittest.mock import patch
from pathlib import Path


def test_load_rec_metadata_df():
    test_df = pd.DataFrame({"age": [20]}, index=["row1"])

    with (patch.object(io, "get_data_path", return_value="/tmp/base"),
          patch.object(io.pd, "read_excel", return_value=test_df) as mock_read):
        out = io.load_rec_metadata_df()

    mock_read.assert_called_once_with("/tmp/base/extra/AMBER_rec_metadata.xlsx", index_col=0)
    assert out.equals(test_df)


def test_load_session_df_wrong_format():
    fpath = Path('session/session_fpath/file.csv')
    with pytest.raises(ValueError):
        io.load_session_df(fpath)


def test_get_sid_from_session_fpath_existance_error():
    fpath = Path("random/non/exiting/dir/session_file.txt")
    with pytest.raises(FileNotFoundError):
        io.load_session_df(fpath)
