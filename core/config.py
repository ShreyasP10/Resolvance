"""Settings per UPDATED_SIH26142_FULL_v2.md:7,12"""
from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

def _env_str(k, d): return os.environ.get(k, d)
def _env_int(k, d):
    try: return int(os.environ.get(k, d) or d)
    except Exception: return d
def _env_float(k, d):
    try: return float(os.environ.get(k, d) or d)
    except Exception: return d
def _env_bool(k, d):
    v=os.environ.get(k)
    return d if v is None else v.strip().lower() in {"1","true","yes","on"}

@dataclass(frozen=True)
class Settings:
    base_dir: Path
    upload_dir: Path
    results_dir: Path
    max_bytes: int
    retention_hours: int | None
    mock_delay_seconds: float
    host: str
    port: int
    debug: bool
    tile_size: int = 256
    overlap: int = 16
    scale: int = 3
    device: str = "cpu"
    model_name: str = "real_esrgan_4ch"
    dropout_p: float = 0.2
    mc_passes: int = 10
    test_mode: bool = False
    allowed_extensions: frozenset = frozenset({".tif",".tiff",".png",".jpg",".jpeg"})
    geotiff_extensions: frozenset = frozenset({".tif",".tiff"})

    @classmethod
    def from_env(cls, base_dir: Path | None = None):
        base = base_dir or Path(__file__).resolve().parent.parent
        up = base / _env_str("SENTINEL_UPLOAD_DIR", "uploads")
        res = base / _env_str("SENTINEL_RESULTS_DIR", "static/results")
        if os.environ.get("VERCEL"):
            up = Path("/tmp") / "uploads"
            res = Path("/tmp") / "results"
        # device auto
        try:
            import torch
            dev = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception: dev = "cpu"
        return cls(
            base_dir=base, upload_dir=up, results_dir=res,
            max_bytes=_env_int("SENTINEL_MAX_FILE_SIZE", 50*1024*1024),
            retention_hours=_env_int("SENTINEL_RETENTION_HOURS", 24),
            mock_delay_seconds=_env_float("SENTINEL_MOCK_DELAY", 0.0),
            host=_env_str("SENTINEL_HOST","0.0.0.0"),
            port=_env_int("SENTINEL_PORT",5000),
            debug=_env_bool("SENTINEL_DEBUG", True),
            tile_size=_env_int("SENTINEL_TILE",256),
            overlap=_env_int("SENTINEL_OVERLAP",16),
            scale=_env_int("SENTINEL_SCALE",3),
            device=dev,
        )

    @classmethod
    def for_test(cls, tmp_root: Path):
        return cls(
            base_dir=tmp_root, upload_dir=tmp_root/"uploads", results_dir=tmp_root/"results",
            max_bytes=50*1024*1024, retention_hours=None, mock_delay_seconds=0.0,
            host="127.0.0.1", port=5000, debug=False, test_mode=True,
        )

    def is_geotiff(self, name: str) -> bool:
        return Path(name).suffix.lower() in self.geotiff_extensions
    def is_allowed(self, name: str) -> bool:
        return Path(name).suffix.lower() in self.allowed_extensions
    def ensure_dirs(self):
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.results_dir.mkdir(parents=True, exist_ok=True)
