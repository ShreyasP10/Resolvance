"""Synthetic degradation SpaceNet 0.5m -> 10m per UPDATED_SIH26142_FULL_v2.md:12"""
from __future__ import annotations
from pathlib import Path
import cv2
import numpy as np
from .io import write_geotiff
from affine import Affine

def degrade(hr: np.ndarray, scale=3, blur_sigma=0.8, noise_std=2.0, transform: Affine | None=None, crs=None) -> np.ndarray:
    # hr C x H x W uint8 0.5m -> synthetic 10m
    C,H,W=hr.shape if hr.ndim==3 else (1,*hr.shape)
    if hr.ndim==2: hr=hr[np.newaxis,:,:]
    # HxWxC for cv2
    hwc=hr.transpose(1,2,0)
    # Gaussian PSF
    blurred=cv2.GaussianBlur(hwc, (7,7), blur_sigma)
    new_h, new_w = H//scale, W//scale
    lr=cv2.resize(blurred, (new_w, new_h), interpolation=cv2.INTER_AREA)
    # add noise
    rng=np.random.default_rng(42)
    noisy=np.clip(lr.astype(float)+rng.normal(0,noise_std, lr.shape),0,255).astype(np.uint8)
    return noisy.transpose(2,0,1) if noisy.ndim==3 else noisy[np.newaxis,:,:]

def degrade_file(hr_path: Path, out_lr: Path, scale=3):
    from .io import read_geotiff
    geo=read_geotiff(hr_path)
    lr=degrade(geo.band, scale=scale)
    # scale transform
    new_t=geo.transform * Affine.scale(scale, scale)
    write_geotiff(out_lr, lr, geo.transform, geo.crs, new_t)
    return out_lr
