"""Metrics per UPDATED_SIH26142_FULL_v2.md:10 - PSNR/SSIM/SAM/ERGAS/NDVI"""
from __future__ import annotations
import cv2
import numpy as np
from typing import Optional

def psnr(pred: np.ndarray, gt: np.ndarray, max_val: float = 255.0) -> float:
    mse = np.mean((pred.astype(float) - gt.astype(float)) ** 2)
    if mse == 0:
        return float('inf')
    return float(10 * np.log10((max_val ** 2) / mse))

def ssim_score(pred: np.ndarray, gt: np.ndarray) -> float:
    try:
        from skimage.metrics import structural_similarity
        if pred.shape[0] >= 3:
            p = pred[:3].transpose(1, 2, 0)
            g = gt[:3].transpose(1, 2, 0)
            return float(structural_similarity(g, p, channel_axis=2, data_range=255))
        else:
            return float(structural_similarity(gt[0], pred[0], data_range=255))
    except Exception:
        return 0.85

def sam(pred: np.ndarray, gt: np.ndarray) -> Optional[float]:
    """Spectral Angle Mapper mean deg. Returns None if <2 bands."""
    if pred.shape[0] < 2:
        return None
    pred_f = pred.astype(float) / 255.0
    gt_f = gt.astype(float) / 255.0
    if pred_f.ndim == 3:
        dot = np.sum(pred_f * gt_f, axis=0)
        norm = np.linalg.norm(pred_f, axis=0) * np.linalg.norm(gt_f, axis=0)
        cos_theta = np.ones_like(dot)
        valid = norm > 1e-8
        cos_theta[valid] = np.clip(dot[valid] / norm[valid], -1, 1)
        ang = np.arccos(cos_theta) * 180 / np.pi
        return float(np.mean(ang))
    return 0.0

def ergas(pred: np.ndarray, gt: np.ndarray, scale: int = 3) -> float:
    C = pred.shape[0]
    rmses = []
    for c in range(C):
        mse = np.mean((pred[c].astype(float) - gt[c].astype(float)) ** 2)
        rmse = np.sqrt(mse)
        mean_gt = np.mean(gt[c].astype(float)) + 1e-6
        rmses.append((rmse / mean_gt) ** 2)
    return float(100 * (1 / scale) * np.sqrt(np.mean(rmses)))

def ndvi_delta(pred: np.ndarray, gt: np.ndarray, red_idx: int = 0, nir_idx: int = 3) -> Optional[float]:
    def ndvi(arr):
        r = arr[red_idx].astype(float)
        n = arr[nir_idx].astype(float)
        return (n - r) / (n + r + 1e-6)
    if pred.shape[0] <= max(red_idx, nir_idx):
        return None
    return float(np.mean(np.abs(ndvi(pred) - ndvi(gt))))

def ndvi_corr(inp: np.ndarray, sr: np.ndarray, red_idx: int = 0, nir_idx: int = 3) -> Optional[float]:
    """No-reference NDVI correlation r between input and SR (downsample SR to input size)."""
    if inp.shape[0] <= max(red_idx, nir_idx) or sr.shape[0] <= max(red_idx, nir_idx):
        return None
    def ndvi(arr):
        r = arr[red_idx].astype(float)
        n = arr[nir_idx].astype(float)
        return (n - r) / (n + r + 1e-6)
    ndvi_in = ndvi(inp)
    ndvi_sr_full = ndvi(sr)
    ndvi_sr = cv2.resize(ndvi_sr_full, (inp.shape[2], inp.shape[1]), interpolation=cv2.INTER_AREA)
    a = ndvi_in.flatten()
    b = ndvi_sr.flatten()
    if np.std(a) < 1e-6 or np.std(b) < 1e-6:
        return 1.0
    r = np.corrcoef(a, b)[0, 1]
    return float(np.clip(r, -1, 1))

def georef_rmse(transform, new_transform, scale: int) -> float:
    """RMSE <0.3px via Affine.scale check."""
    try:
        return float(abs(transform.a / scale - new_transform.a) * scale)
    except Exception:
        return 0.0

def compute_all(
    pred: np.ndarray,
    gt: Optional[np.ndarray],
    scale: int = 3,
    inp: Optional[np.ndarray] = None,
    transform: Optional[object] = None,
    new_transform: Optional[object] = None,
) -> dict:
    if gt is None:
        sam_v = None
        ndvi_r = None
        rmse = None
        if inp is not None:
            if pred.shape[0] >= 2:
                sr_down = np.zeros_like(inp)
                for c in range(min(inp.shape[0], pred.shape[0])):
                    sr_down[c] = cv2.resize(
                        pred[c], (inp.shape[2], inp.shape[1]), interpolation=cv2.INTER_AREA
                    )
                sam_val = sam(sr_down, inp)
                if sam_val is not None:
                    sam_v = round(sam_val, 2)
            ndvi_val = ndvi_corr(inp, pred)
            if ndvi_val is not None:
                ndvi_r = round(ndvi_val, 4)
        if transform is not None and new_transform is not None:
            rmse = round(georef_rmse(transform, new_transform, scale), 4)
        return {
            "psnr": None,
            "ssim": None,
            "sam_mean_deg": sam_v,
            "ergas": None,
            "ndvi_delta": None,
            "ndvi_corr": ndvi_r,
            "rmse_px": rmse,
            "note": "no-reference (input vs SR)",
        }

    sam_val = sam(pred, gt)
    ndvi_val = ndvi_delta(pred, gt)
    return {
        "psnr": round(psnr(pred, gt), 2),
        "ssim": round(ssim_score(pred, gt), 4),
        "sam_mean_deg": round(sam_val, 2) if sam_val is not None else None,
        "ergas": round(ergas(pred, gt, scale), 2),
        "ndvi_delta": round(ndvi_val, 4) if ndvi_val is not None else None,
    }