"""Pipeline per UPDATED_SIH26142_FULL_v2.md:10-12 - tiling + stitch + heatmap"""
from __future__ import annotations
import base64
import time
import uuid
from pathlib import Path
from typing import Optional

import numpy as np
from affine import Affine

from .config import Settings
from .exceptions import DecodingError, ProcessingError
from .io import read_geotiff, read_image, normalize_to_uint8_per_band, write_geotiff, write_png
from .patch import TileManager
from .transforms import SRModel, super_resolve, uncertainty
from .metrics import compute_all
from .models import FileType, ImageSet, InferenceResult, JobMeta
from .logging_setup import get_logger

class Pipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.ensure_dirs()
        self.tile_mgr = TileManager(settings.tile_size, settings.overlap)
        self.sr_model = SRModel(scale=settings.scale, device=settings.device)

    def run(self, input_path: Path, job_id: Optional[str] = None) -> InferenceResult:
        if job_id is None:
            job_id = uuid.uuid4().hex
        short = job_id[:8]
        log = get_logger("pipeline")
        log.info(f"[{short}] ingest {input_path.name}")
        is_geo = self.settings.is_geotiff(input_path.name)
        start = time.perf_counter()
        try:
            if is_geo:
                result = self._process_geotiff(input_path, job_id, log)
            else:
                result = self._process_image(input_path, job_id, log)
        except (DecodingError, ProcessingError):
            raise
        except Exception as e:
            raise ProcessingError(f"Pipeline failure: {e}") from e
        result.meta.elapsed = round(time.perf_counter() - start, 1)
        log.info(f"[{short}] complete {result.meta.elapsed}s")
        return result

    def _process_geotiff(self, path: Path, job_id: str, log) -> InferenceResult:
        from .io import GeoReadResult
        geo = read_geotiff(path)
        norm = normalize_to_uint8_per_band(geo.band)
        crs_label = str(geo.crs) if geo.crs else "Unknown"
        log.info(f"[{job_id[:8]}] GeoTIFF {geo.width}x{geo.height}x{geo.count} CRS {crs_label}")
        tiles = self.tile_mgr.tile(norm)
        log.info(f"[{job_id[:8]}] tiled {len(tiles)}")
        sr_tiles = []
        coords = []
        for t in tiles:
            sr = super_resolve(t.data, self.sr_model, scale=self.settings.scale)
            sr_tiles.append(sr)
            coords.append(t.coords)
        out_h, out_w = geo.height * self.settings.scale, geo.width * self.settings.scale
        sr_arr = self.tile_mgr.stitch(sr_tiles, coords, out_h, out_w, self.settings.scale)
        heat = uncertainty(norm, self.sr_model, T=self.settings.mc_passes)
        import cv2
        heat_sr = cv2.resize(heat, (out_w, out_h), interpolation=cv2.INTER_CUBIC)
        new_transform = geo.transform * Affine.scale(geo.width / out_w, geo.height / out_h)
        metrics = compute_all(
            sr_arr, None, scale=self.settings.scale, inp=norm,
            transform=geo.transform, new_transform=new_transform
        )
        input_png = self.settings.results_dir / f"{job_id}_input.png"
        sr_png = self.settings.results_dir / f"{job_id}_sr.png"
        heat_png = self.settings.results_dir / f"{job_id}_heatmap.png"
        write_png(input_png, norm)
        write_png(sr_png, sr_arr)
        heat_color = cv2.applyColorMap(heat_sr, cv2.COLORMAP_VIRIDIS)
        heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGB)
        heat_cx = heat_color.transpose(2, 0, 1)
        write_png(heat_png, heat_cx)
        tif_path = self.settings.results_dir / f"{job_id}_sr.tif"
        write_geotiff(tif_path, sr_arr, geo.transform, geo.crs, new_transform)
        heat_tif = self.settings.results_dir / f"{job_id}_heatmap.tif"
        write_geotiff(heat_tif, heat_sr[np.newaxis, :, :], geo.transform, geo.crs, new_transform)
        return InferenceResult(
            job_id=job_id,
            images=ImageSet(
                input=self._data_url(input_png),
                sr=self._data_url(sr_png),
                heatmap=self._data_url(heat_png),
            ),
            download_png=self._dl(f"{job_id}_sr.png"),
            download_tif=self._dl(f"{job_id}_sr.tif"),
            download_heatmap=self._dl(f"{job_id}_heatmap.tif"),
            meta=JobMeta(
                job_id=job_id,
                input_size=f"{geo.width}x{geo.height}x{geo.count}",
                output_size=f"{out_w}x{out_h}x{sr_arr.shape[0]}",
                crs=crs_label,
                elapsed=0.0,
                file_type=FileType.GEOTIFF,
            ),
            metrics=metrics,
        )

    def _process_image(self, path: Path, job_id: str, log) -> InferenceResult:
        arr = read_image(path)
        norm = normalize_to_uint8_per_band(arr)
        h, w = norm.shape[1], norm.shape[2]
        tiles = self.tile_mgr.tile(norm)
        sr_tiles = []
        coords = []
        for t in tiles:
            sr = super_resolve(t.data, self.sr_model, scale=self.settings.scale)
            sr_tiles.append(sr)
            coords.append(t.coords)
        out_h, out_w = h * self.settings.scale, w * self.settings.scale
        sr_arr = self.tile_mgr.stitch(sr_tiles, coords, out_h, out_w, self.settings.scale)
        import cv2
        heat = uncertainty(norm, self.sr_model)
        heat_sr = cv2.resize(heat, (out_w, out_h), interpolation=cv2.INTER_CUBIC)
        metrics = compute_all(sr_arr, None, scale=self.settings.scale, inp=norm, transform=None, new_transform=None)
        input_png = self.settings.results_dir / f"{job_id}_input.png"
        sr_png = self.settings.results_dir / f"{job_id}_sr.png"
        heat_png = self.settings.results_dir / f"{job_id}_heatmap.png"
        write_png(input_png, norm)
        write_png(sr_png, sr_arr)
        heat_color = cv2.applyColorMap(heat_sr, cv2.COLORMAP_VIRIDIS)
        heat_color = cv2.cvtColor(heat_color, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)
        write_png(heat_png, heat_color)
        return InferenceResult(
            job_id=job_id,
            images=ImageSet(
                input=self._data_url(input_png),
                sr=self._data_url(sr_png),
                heatmap=self._data_url(heat_png),
            ),
            download_png=self._dl(f"{job_id}_sr.png"),
            download_tif=None,
            download_heatmap=None,
            meta=JobMeta(
                job_id=job_id,
                input_size=f"{w}x{h}x{norm.shape[0]}",
                output_size=f"{out_w}x{out_h}x{sr_arr.shape[0]}",
                crs="Unknown",
                elapsed=0.0,
                file_type=FileType.IMAGE,
            ),
            metrics=metrics,
        )

    def _data_url(self, p: Path) -> str:
        b64 = base64.b64encode(p.read_bytes()).decode("ascii")
        return f"data:image/png;base64,{b64}"

    def _dl(self, name: str) -> str:
        return f"/api/download/{name}"