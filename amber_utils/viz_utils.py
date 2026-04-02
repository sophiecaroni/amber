import matplotlib.pyplot as plt
import amber_utils.io_utils as io
from contextlib import contextmanager
from matplotlib.figure import Figure
from amber_utils.io_utils import set_for_save
from pathlib import Path


@contextmanager
def plot_context():
    params = {
        'figure.dpi': 300,
        'axes.grid': False,
        'font.size': 7,
        'axes.titlesize': 7,
        'figure.titlesize': 9,
        'axes.labelsize': 7,
        'xtick.labelsize': 6,
        'ytick.labelsize': 6,
        'legend.fontsize': 5,
        'legend.title_fontsize': 5,
        'axes.linewidth': 1,
        'xtick.major.width': 1,
        'ytick.major.width': 1,
        'xtick.major.size': 2,
        'ytick.major.size': 2,
    }
    style_path = Path(__file__).resolve().parent.parent / 'viz' / 'despine.mplstyle'
    with plt.rc_context(rc=params), plt.style.context(str(style_path)):
        yield


def save_figure(
        save_dir: str | None,
        fname: str,
        fig: Figure | None = None,
        dpi: int = 900,
        **kwargs,
) -> None:
    outputs_path = io.get_figures_path()
    if save_dir is not None:
        outputs_path /= save_dir

    save_path = set_for_save(outputs_path)

    # Remove extension if any and (re-) add .png
    fname = f'{Path(fname).stem}.png'

    # Define final path
    full_save_path = save_path / fname

    if fig is None:
        plt.savefig(full_save_path, dpi=dpi, **kwargs)
    else:
        fig.savefig(full_save_path, dpi=dpi, **kwargs)


def get_cuing_palette():
    return {'rinval': '#ed6189', 'rval': '#63db83'}


def get_att_palette():
    return {'audio_vis': '#55faf7', 'vis_sel': '#73b2fa', 'spat': '#81fa7f'}


def get_group_palette():
    return {'adults': '#558fe6', 'children': '#eca1ed'}


def get_hue_palette(hue: str) -> dict:
    hue = hue.lower()
    if hue == 'cueing':
        return get_cuing_palette()
    elif hue.startswith('att'):
        return get_att_palette()
    elif hue == 'group':
        return get_group_palette()
    else:
        raise ValueError(f'Custom palette missing for {hue = }')


def get_interv_label(interv: str) -> str:
    return {
        'VR': 'VR-based training',
        'OA': 'Occlusion therapy'
    }[interv]


def get_econd_label(econd: str) -> str:
    return {
        'DO': 'Dominant eye',
        'ND': 'Non-dominant eye',
    }[econd]


def get_att_type_label(att_type: str) -> str:
    return {
        'audio_vis': 'Audiovisual',
        'vis_sel': 'Visual selective',
        'spat': 'Spatial',
    }[att_type]

