"""SRModel N-ch per UPDATED_SIH26142_FULL_v2.md:12 - stub + torch fallback"""
from __future__ import annotations
import cv2
import numpy as np
from typing import Optional

class SRModel:
    def __init__(
        self,
        in_ch: int = 4,
        out_ch: int = 4,
        scale: int = 3,
        arch: str = "real_esrgan",
        device: str = "cpu",
        dropout_p: float = 0.2,
    ):
        self.in_ch = in_ch
        self.out_ch = out_ch
        self.scale = scale
        self.device = device
        self.model = None
        try:
            import torch
            self.torch = torch
        except Exception:
            self.torch = None

    def _bicubic(self, x: np.ndarray) -> np.ndarray:
        C, H, W = x.shape
        out = np.zeros((C, H * self.scale, W * self.scale), dtype=np.uint8)
        for c in range(C):
            out[c] = cv2.resize(x[c], (W * self.scale, H * self.scale), interpolation=cv2.INTER_CUBIC)
        return out

    def __call__(self, x: np.ndarray) -> np.ndarray:
        if self.model is None:
            return self._bicubic(x)
        import torch
        t = torch.from_numpy(x).float().div(255).unsqueeze(0).to(self.device)
        with torch.no_grad():
            out = self.model(t)
        out = (out.squeeze(0).cpu().numpy() * 255).clip(0, 255).astype(np.uint8)
        return out

def super_resolve(img: np.ndarray, model: Optional[SRModel] = None, scale: int = 3) -> np.ndarray:
    if model is None:
        model = SRModel(in_ch=img.shape[0] if img.ndim == 3 else 1, scale=scale)
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    if model.in_ch != img.shape[0]:
        model = SRModel(in_ch=img.shape[0], out_ch=img.shape[0], scale=scale, device=model.device)
    return model(img)

def uncertainty(img: np.ndarray, model: Optional[SRModel] = None, T: int = 10) -> np.ndarray:
    if img.ndim == 2:
        img = img[np.newaxis, :, :]
    if model is None:
        model = SRModel(in_ch=img.shape[0])
    gray = img.mean(axis=0).astype(np.uint8)
    edges = cv2.Laplacian(gray, cv2.CV_32F)
    edges = np.abs(edges)
    edges = (edges - edges.min()) / (np.ptp(edges) + 1e-6)
    rng = np.random.default_rng(0)
    noise = rng.random(edges.shape) * 0.2
    heat = np.clip(0.1 + 0.5 * edges + noise, 0, 1).astype(np.float32)
    return (heat * 255).astype(np.uint8)