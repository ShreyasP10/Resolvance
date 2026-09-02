import os
import argparse
import torch
from torch.utils.data import Dataset, DataLoader
from torch.optim import Adam
import numpy as np
import cv2
from pathlib import Path
import random

from core.io import read_image, read_geotiff, normalize_to_uint8_per_band
from core.ml_models import NChannelRRDBNet, CombinedSRLoss

class SelfSupervisedDegradationDataset(Dataset):
    """
    Simulates Sentinel-2 point spread function and sensor noise.
    Takes high-res patches, degrades them (blur, downsample, noise) 
    to create (LR, HR) training pairs dynamically.
    """
    def __init__(self, data_dir, patch_size=256, scale=3, in_nc=4):
        self.data_dir = Path(data_dir)
        self.files = list(self.data_dir.glob("*.tif")) + list(self.data_dir.glob("*.png"))
        self.patch_size = patch_size
        self.scale = scale
        self.in_nc = in_nc
        
        # Load everything into memory for fast hackathon training, or load lazily.
        # We will load lazily here since GeoTIFFs can be huge.

    def __len__(self):
        # Return an arbitrary epoch length based on number of files
        return len(self.files) * 20

    def _degrade(self, hr_patch):
        # hr_patch: C x H x W (float32, 0-1)
        C, H, W = hr_patch.shape
        lr_h, lr_w = H // self.scale, W // self.scale
        
        lr_patch = np.zeros((C, lr_h, lr_w), dtype=np.float32)
        for c in range(C):
            # Apply slight Gaussian blur (point spread function proxy)
            k_size = random.choice([3, 5])
            sigma = random.uniform(0.5, 1.5)
            blurred = cv2.GaussianBlur(hr_patch[c], (k_size, k_size), sigma)
            # Area-averaging downsample (NOT bicubic) to mimic sensor binning
            lr = cv2.resize(blurred, (lr_w, lr_h), interpolation=cv2.INTER_AREA)
            
            # Add sensor noise
            noise = np.random.normal(0, random.uniform(0, 0.02), lr.shape)
            lr_patch[c] = np.clip(lr + noise, 0.0, 1.0)
            
        return lr_patch

    def __getitem__(self, idx):
        file_idx = idx % len(self.files)
        path = self.files[file_idx]
        
        try:
            if path.suffix.lower() in ['.tif', '.tiff']:
                res = read_geotiff(path)
                img = normalize_to_uint8_per_band(res.band)
            else:
                img = read_image(path)
                
            # Ensure C x H x W
            if img.ndim == 2: img = img[np.newaxis, :, :]
            C, H, W = img.shape
            
            # Pad if too small
            if H < self.patch_size or W < self.patch_size:
                img = np.pad(img, ((0,0), (0, max(0, self.patch_size - H)), (0, max(0, self.patch_size - W))), mode='reflect')
                H, W = img.shape[1:]
                
            # Random crop
            y = random.randint(0, H - self.patch_size)
            x = random.randint(0, W - self.patch_size)
            hr_crop = img[:self.in_nc, y:y+self.patch_size, x:x+self.patch_size].astype(np.float32) / 255.0
            
            # Data augmentation (flip/rotate)
            if random.random() > 0.5:
                hr_crop = np.flip(hr_crop, axis=1).copy()
            if random.random() > 0.5:
                hr_crop = np.flip(hr_crop, axis=2).copy()
                
            # Create LR
            lr_crop = self._degrade(hr_crop)
            
            return torch.from_numpy(lr_crop), torch.from_numpy(hr_crop)
            
        except Exception as e:
            # Fallback on dummy data if read fails
            lr_crop = np.zeros((self.in_nc, self.patch_size//self.scale, self.patch_size//self.scale), dtype=np.float32)
            hr_crop = np.zeros((self.in_nc, self.patch_size, self.patch_size), dtype=np.float32)
            return torch.from_numpy(lr_crop), torch.from_numpy(hr_crop)

def train():
    parser = argparse.ArgumentParser(description="Train N-Channel RRDBNet SR Model")
    parser.add_argument("--data_dir", type=str, default="sample", help="Path to high-res training images")
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch_size", type=int, default=8)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--scale", type=int, default=3)
    parser.add_argument("--in_nc", type=int, default=4)
    parser.add_argument("--save_path", type=str, default="weights/real_esrgan_4ch.pth")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.save_path), exist_ok=True)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Training on {device}...")

    # Initialize model
    model = NChannelRRDBNet(in_nc=args.in_nc, out_nc=args.in_nc, scale=args.scale).to(device)
    
    # Initialize Combined Loss (L1 + Perceptual + SAM)
    criterion = CombinedSRLoss(lambda_l1=1.0, lambda_perceptual=0.1, lambda_sam=0.05).to(device)
    optimizer = Adam(model.parameters(), lr=args.lr)
    
    dataset = SelfSupervisedDegradationDataset(args.data_dir, scale=args.scale, in_nc=args.in_nc)
    dataloader = DataLoader(dataset, batch_size=args.batch_size, shuffle=True, num_workers=0)
    
    for epoch in range(args.epochs):
        model.train()
        epoch_loss = 0.0
        
        for batch_idx, (lr, hr) in enumerate(dataloader):
            lr, hr = lr.to(device), hr.to(device)
            
            optimizer.zero_grad()
            sr = model(lr)
            
            loss = criterion(sr, hr)
            loss.backward()
            optimizer.step()
            
            epoch_loss += loss.item()
            
            if batch_idx % 10 == 0:
                print(f"Epoch [{epoch+1}/{args.epochs}] Batch [{batch_idx}/{len(dataloader)}] Loss: {loss.item():.4f}")
                
        print(f"===> Epoch {epoch+1} Complete: Avg Loss {epoch_loss/len(dataloader):.4f}")
        torch.save(model.state_dict(), args.save_path)
        print(f"Saved weights to {args.save_path}")

if __name__ == "__main__":
    train()
