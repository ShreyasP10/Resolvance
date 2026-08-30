"""N-band IO per UPDATED_SIH26142_FULL_v2.md:9,10 - fresh, no raw[:,:,0] debt"""
from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import cv2
import numpy as np
import tifffile
from affine import Affine
from .exceptions import DecodingError

@dataclass
class GeoReadResult:
    band: np.ndarray  # C x H x W uint8/float
    transform: Affine
    crs: object
    width: int
    height: int
    count: int

def _extract_affine(page) -> Affine:
    for tag in page.tags:
        if tag.code == 34264:
            val = list(tag.value)
            if len(val) >= 6:
                scale_tag = page.tags.get(33550)
                scale = list(scale_tag.value) if scale_tag else [1.0, 1.0, 0.0]
                return Affine.translation(val[3], val[4]) * Affine.scale(scale[0], -scale[1])
            if len(val) >= 16:
                return Affine(val[0], val[1], val[3], val[4], val[5], val[7])
    return Affine.identity()

def _extract_crs(page) -> object:
    for tag in page.tags:
        if tag.code == 34735:
            vals = list(tag.value)
            if len(vals) >= 6:
                epsg = _geo_key(vals, 3072) or _geo_key(vals, 2048)
                if epsg: return f"EPSG:{epsg}"
    return None

def _geo_key(keys, kid):
    for i in range(0, len(keys), 4):
        if i+3 < len(keys) and keys[i]==kid and keys[i+1]==0:
            return keys[i+3]
    return None

def read_geotiff(path: Path) -> GeoReadResult:
    try:
        with tifffile.TiffFile(str(path)) as tif:
            page = tif.pages[0]
            raw = tif.asarray()  # full stack: handles multi-page planar (4,64,64)
            # Normalize to C x H x W
            if raw.ndim == 2:
                band = raw[np.newaxis, :, :]  # 1 x H x W
                count = 1
            elif raw.ndim == 3:
                # tifffile planar vs interleaved heuristic
                # planar: C x H x W where C small (1,3,4,8) and H,W large
                # interleaved: H x W x C
                # Use smallest dim as channel if <=8
                if raw.shape[0] <= 8 and raw.shape[0] < raw.shape[1] and raw.shape[0] < raw.shape[2]:
                    band = raw  # already C x H x W
                    count = raw.shape[0]
                elif raw.shape[2] <= 8:
                    band = raw.transpose(2,0,1)  # HxWxC -> CxHxW
                    count = raw.shape[2]
                else:
                    # fallback planar
                    band = raw
                    count = raw.shape[0]
            else:
                raise DecodingError(f"Unsupported ndim {raw.ndim}")
            return GeoReadResult(
                band=band.astype(np.uint8) if band.dtype==np.uint8 else band,
                transform=_extract_affine(page),
                crs=_extract_crs(page),
                width=page.imagewidth,
                height=page.imagelength,
                count=count,
            )
    except DecodingError: raise
    except Exception as e:
        raise DecodingError(f"Could not read GeoTIFF {path.name}: {e}") from e

def read_image(path: Path) -> np.ndarray:
    try:
        img = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)
        if img is None: raise DecodingError(f"Could not decode {path.name}")
        if img.ndim == 2:
            return img[np.newaxis, :, :]  # 1 x H x W
        elif img.ndim == 3:
            # BGR -> RGB -> CxHxW
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            return rgb.transpose(2,0,1)
        return img
    except DecodingError: raise
    except Exception as e:
        raise DecodingError(f"Could not decode {path.name}: {e}") from e

def normalize_to_uint8_per_band(arr: np.ndarray) -> np.ndarray:
    """Per-band 2-98 percentile clip per UPDATED_SIH26142_FULL_v2.md:12"""
    if arr.ndim == 2: arr = arr[np.newaxis, :, :]
    out = np.empty(arr.shape, dtype=np.uint8)
    for c in range(arr.shape[0]):
        band = arr[c].astype(np.float32)
        valid = band[np.isfinite(band)]
        if valid.size == 0:
            out[c]=np.zeros_like(band, dtype=np.uint8)
            continue
        lo, hi = np.percentile(valid, [2,98])
        if hi <= lo: lo, hi = float(valid.min()), float(valid.max())
        if hi <= lo:
            out[c]=np.zeros_like(band, dtype=np.uint8)
            continue
        scaled = np.clip((band-lo)/(hi-lo),0,1)
        out[c]=(scaled*255).astype(np.uint8)
    return out

def write_png(path: Path, arr: np.ndarray):
    # arr C x H x W or H x W
    if arr.ndim == 3:
        if arr.shape[0] == 1:
            img = arr[0]
        elif arr.shape[0] == 3:
            rgb = arr.transpose(1,2,0)
            img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        elif arr.shape[0] >= 4:
            # 4/8-band: preview first 3 bands
            rgb = arr[:3].transpose(1,2,0)
            img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        else:
            # generic C x H x W -> take mean for preview
            img = arr.mean(axis=0).astype(np.uint8)
    else: img = arr
    cv2.imwrite(str(path), img)

def _geotiff_tags(transform: Affine, crs, h, w):
    tags=[]
    if crs:
        epsg = str(crs).replace("EPSG:","")
        try: epsg_int=int(epsg)
        except Exception: epsg_int=4326
        keys=[1024,0,1,2, 1025,0,1,1, 2048,0,1,epsg_int, 2054,0,1,9102, 3072,0,1,epsg_int, 3076,0,1,9001]
        tags.append((34735,3,len(keys),keys,True))
    tags.append((33550,12,3,(transform[0], abs(transform[4]),0.0),True))
    tags.append((33922,12,6,(0.0,0.0,0.0,transform[2],transform[5],0.0),True))
    return tags

def write_geotiff(path: Path, arr: np.ndarray, transform: Affine, crs, new_transform: Optional[Affine]=None):
    """Planar C x H x W per v2:10 SDD"""
    if arr.ndim == 2: arr = arr[np.newaxis, :, :]
    if arr.ndim !=3: raise ValueError(f"Expected C x H x W got {arr.shape}")
    h,w = arr.shape[1], arr.shape[2]
    tf = new_transform if new_transform is not None else transform
    tags=_geotiff_tags(tf,crs,h,w)
    # photometric: minisblack for 1 band, rgb for 3
    if arr.shape[0]==3: photo="rgb"
    else: photo="minisblack"
    tifffile.imwrite(str(path), arr, extratags=tags, photometric=photo)
