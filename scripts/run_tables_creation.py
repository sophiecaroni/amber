import amber_utils.io_utils as io
from amber.features import extract_all_sessions
from amber.features.attention_extraction import extract_attention_features
from amber.features.performance_extraction import extract_performance_features


def extract_all_session_perf_table(test: bool, save: bool = False):
    all_session_perf_df = extract_all_sessions(extract_performance_features, test)

    if save:
        out_dir = io.get_results_path()
        fname = 'performance_summary.csv'
        all_session_perf_df.to_csv(out_dir / fname)
        print(f'\n\tExporting {fname}...\n\tSaved ✅')
    else:
        print(
            f"\nFinal df: \n\t{all_session_perf_df}"
        )


def extract_all_session_att_table(test: bool, save: bool = False):
    all_session_att_df = extract_all_sessions(extract_attention_features, test)

    if save:
        out_dir = io.get_results_path()
        fname = 'attention_features.csv'
        all_session_att_df.to_csv(out_dir / fname)
        print(f'\n\tExporting {fname}...\n\tSaved ✅')
    else:
        print(
            f"\nFinal df: \n\t{all_session_att_df}"
        )


def extract_tables(**kwargs) -> None:
    extract_all_session_perf_table(**kwargs)
    extract_all_session_att_table(**kwargs)


if __name__ == '__main__':
    extract_tables(
        test=False,
        save=True,
    )


