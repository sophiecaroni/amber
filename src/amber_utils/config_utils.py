import configparser
from pathlib import Path


def load_config(
        config_path: str | None = None
) -> configparser.ConfigParser:
    cfg = configparser.ConfigParser()

    # Gets the config.ini existing in the closest directory to the calling script
    if config_path is None:
        search_roots = [Path.cwd(), *Path.cwd().parents, *Path(__file__).resolve().parents]
        for parent in search_roots:
            candidate = parent / "config.ini"
            if candidate.exists():
                config_path = candidate
                break
        else:
            raise FileNotFoundError("config.ini not found in any parent directory")
    else:
        config_path = Path(config_path)

    cfg.read(config_path)
    return cfg


def get_local_root(config_path: str | None = None) -> Path:
    cfg = load_config(config_path)
    root = cfg.get("Paths", "local_root", fallback=str(Path.home() / "local"))
    return Path(root)
