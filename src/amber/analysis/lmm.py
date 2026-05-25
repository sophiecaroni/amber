"""
    Title: Linear mixed models (LMM)

    Author: Sophie Caroni
    Date of creation: 10.03.2026

    Description:
    This script contains functions that allow to parametrize and run LMMs.
"""
import subprocess
import amber_utils.io_utils as io
from pathlib import Path


def run_rscript(rscript_fname: str, args: list, verbose: bool = True) -> subprocess.CompletedProcess:
    r_script_path = Path(__file__).resolve().parent / rscript_fname
    r_executable = Path("/Library/Frameworks/R.framework/Resources/bin/Rscript")

    args_str = [str(arg).lower() if isinstance(arg, bool) else str(arg) for arg in args]

    try:
        result = subprocess.run(
            args=[str(r_executable), str(r_script_path)] + args_str,
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as e:
        print("R script failed")
        print("stdout:")
        print(e.stdout)
        print("stderr:")
        print(e.stderr)
        raise

    if verbose:
        print("\n####################################### R SCRIPT OUTPUT #######################################\n")
        print(result.stdout)
        if result.stderr:
            print("####################################### R SCRIPT WARNINGS ######################################\n")
            print(result.stderr)
    return result


def _parse_rscript_output(output: str, pattern: str) -> str:
    for line in output.splitlines():
        if pattern in line:
            return line.split(pattern, 1)[1].strip()
    raise RuntimeError(f"Could not find value with prefix '{pattern}' from R output.")


def select_best_fit_method() -> str:
    df_path = io.get_tables_path() / 'performance_summary.csv'
    script_out = run_rscript(
        "eval_lmm_fits.R",[df_path], verbose=True,
    )
    return _parse_rscript_output(script_out.stdout, "PROPOSED_BEST_FIT_METHOD=")


def rt_lmm(rt_metric_col: str, save: bool = False, verbose: bool = False) -> None:
    data_path = io.get_tables_path() / 'performance_summary.csv'
    script_out = run_rscript(
        "lmm_pipeline.R",[rt_metric_col, data_path, verbose, save], verbose=verbose,
    )
    best_model = _parse_rscript_output(script_out.stdout, "SELECTED_MODEL=")
    print(f'BEST MODEL: {best_model}')


def rt_post_hocs(rt_metric_col: str, save: bool = False, verbose: bool = False) -> None:
    anova_path = io.get_stats_path() / f'anova_{rt_metric_col}.csv'
    model_path = io.get_stats_path() / f'model_{rt_metric_col}.rds'
    script_out = run_rscript(
        "lmm_posthoc.R", [rt_metric_col, anova_path, model_path, verbose, save], verbose=verbose,
    )


def att_lmm(rt_metric_col: str, save: bool = False, verbose: bool = False) -> None:
    data_path = io.get_tables_path() / 'attention_features.csv'
    script_out = run_rscript(
        "att_lmm_pipeline.R", [rt_metric_col, data_path, verbose, save], verbose=verbose,
    )
