from dataclasses import dataclass
from pathlib import Path
import tomllib

PIPELINE_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = PIPELINE_DIR.parent

@dataclass
class Config:
    cache_path: Path
    content_path: Path
    gold_path: Path
    image_width: int
    max_age_days: int
    media_path: Path
    output_path: Path
    stations_path: Path
    timeout_seconds: float
    user_agent: str

def load_config(
    pipeline_dir: Path = PIPELINE_DIR,
    repo_root: Path = REPO_ROOT
) -> Config:
    values = _read_toml(pipeline_dir / "defaults.toml")
    values = _merge(values, _read_toml(pipeline_dir / "config.toml"))
    return Config(
        cache_path = _resolve(repo_root, values["cache"]["path"]),
        content_path = _resolve(repo_root, values["content"]["path"]),
        gold_path = _resolve(repo_root, values["explorer"]["gold_path"]),
        image_width = int(values["media"]["image_width"]),
        max_age_days = int(values["cache"]["max_age_days"]),
        media_path = _resolve(repo_root, values["cache"]["media_path"]),
        output_path = _resolve(repo_root, values["output"]["path"]),
        stations_path = _resolve(repo_root, values["explorer"]["stations_path"]),
        timeout_seconds = float(values["http"]["timeout_seconds"]),
        user_agent = values["http"]["user_agent"]
    )

def _merge(base: dict, override: dict) -> dict:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge(merged[key], value)
        else:
            merged[key] = value
    return merged

def _read_toml(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("rb") as file:
        return tomllib.load(file)

def _resolve(repo_root: Path, value: str) -> Path:
    path = Path(value).expanduser()
    return path if path.is_absolute() else repo_root / path
