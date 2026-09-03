from __future__ import annotations
import os
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
        weights_path: Optional[str] = "weights/real_esrgan_4ch.pth",
    ):
        self.in_ch = in_ch
        self.out_ch = out_ch
        self.scale = scale
        self.device = device
        self.model = None
        try:
            import torch
            self.torch = torch
            from .ml_models import NChannelRRDBNet
            # Initialize real model
            model = NChannelRRDBNet(in_nc=in_ch, out_nc=out_ch, scale=scale, dropout_p=dropout_p)
            model = model.to(device)
            
            # Load weights if available
            if weights_path and os.path.exists(weights_path):
                if in_ch == 4:
                    model.load_state_dict(torch.load(weights_path, map_location=device))
                    model.eval()
                    self.model = model
                    print(f"✅ Successfully loaded AI weights from {weights_path} (4-channels)")
                else:
                    print(f"⚠️ Warning: Uploaded {in_ch}-channel image, but weights are for 4-channels. Falling back to bicubic.")
            else:
                print(f"ℹ️ No weights found at {weights_path}. Falling back to bicubic.")
        except ImportError:
            print("❌ PyTorch is not installed locally! Run 'pip install torch' to use the AI model. Falling back to bicubic.")
        except Exception as e:
            print(f"❌ Failed to load PyTorch model: {e}. Falling back to bicubic.")

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
    
    # Real MC-Dropout implementation if model is loaded
    if model.model is not None:
        import torch
        t = torch.from_numpy(img).float().div(255).unsqueeze(0).to(model.device)
        # Enable dropout during inference
        model.model.train() 
        preds = []
        with torch.no_grad():
            for _ in range(T):
                preds.append(model.model(t))
        # preds: List of BxCxHxW
        stacked = torch.stack(preds) # TxBxCxHxW
        # Calculate per-pixel standard deviation across T passes
        std = torch.std(stacked, dim=0) # BxCxHxW
        std_mean = std.squeeze(0).mean(dim=0).cpu().numpy() # HxW
        model.model.eval() # restore eval mode
        
        # Normalize to 0-255 heatmap
        heat = (std_mean - std_mean.min()) / (std_mean.ptp() + 1e-6)
        return (heat * 255).astype(np.uint8)

    # Fallback simulated uncertainty (if no weights loaded or no torch)
    gray = img.mean(axis=0).astype(np.uint8)
    edges = cv2.Laplacian(gray, cv2.CV_32F)
    edges = np.abs(edges)
    edges = (edges - edges.min()) / (np.ptp(edges) + 1e-6)
    rng = np.random.default_rng(0)
    noise = rng.random(edges.shape) * 0.2
    heat = np.clip(0.1 + 0.5 * edges + noise, 0, 1).astype(np.float32)
    return (heat * 255).astype(np.uint8)