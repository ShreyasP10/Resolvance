"""TileManager 256+16 Gaussian per UPDATED_SIH26142_FULL_v2.md:10-12"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np

@dataclass
class Tile:
    data: np.ndarray  # C x 256 x 256
    coords: tuple[int,int]  # (x,y) in input
    weight: np.ndarray  # 256 x 256 float

class TileManager:
    def __init__(self, tile_size=256, overlap=16):
        self.tile_size=tile_size
        self.overlap=overlap
        self.stride=tile_size-overlap

    def _weight_map(self):
        # Hann-like Gaussian but ensure min >0 to avoid zero division at corners
        sigma=self.overlap/2 if self.overlap>0 else self.tile_size/4
        ax=np.linspace(-1,1,self.tile_size)
        xx,yy=np.meshgrid(ax,ax)
        w=np.exp(-(xx**2+yy**2)/(2*(sigma/self.tile_size*2)**2))
        if self.overlap==0: w=np.ones((self.tile_size,self.tile_size),dtype=np.float32)
        else: w=w.astype(np.float32)
        w/=w.max()
        # clamp min to 0.1 so corners still contribute
        w = w*0.9 + 0.1
        return w.astype(np.float32)

    def tile(self, img: np.ndarray) -> list[Tile]:
        # img C x H x W - handles small images
        if img.ndim==2: img=img[np.newaxis,:,:]
        C,H,W=img.shape
        wmap=self._weight_map()
        # If image fits in one tile, return single centered tile with reflect pad
        if H <= self.tile_size and W <= self.tile_size:
            pad_h = self.tile_size - H
            pad_w = self.tile_size - W
            top = pad_h//2; bottom = pad_h - top
            left = pad_w//2; right = pad_w - left
            patch = np.pad(img, ((0,0),(top,bottom),(left,right)), mode='symmetric')
            return [Tile(data=patch, coords=(-left,-top), weight=wmap)]
        # Pad small dim to tile_size if needed
        pad_h = max(0, self.tile_size - H)
        pad_w = max(0, self.tile_size - W)
        top = pad_h//2
        left = pad_w//2
        if pad_h>0 or pad_w>0:
            bottom = pad_h - top
            right = pad_w - left
            img = np.pad(img, ((0,0),(top,bottom),(left,right)), mode='symmetric')
            H,W = img.shape[1], img.shape[2]
        tiles=[]
        for y in range(0, H, self.stride):
            for x in range(0, W, self.stride):
                x2=min(x+self.tile_size, W)
                y2=min(y+self.tile_size, H)
                x1=x2-self.tile_size
                y1=y2-self.tile_size
                patch=np.zeros((C,self.tile_size,self.tile_size),dtype=img.dtype)
                sx0=max(0,x1); sy0=max(0,y1)
                dx0=sx0-x1; dy0=sy0-y1
                sx1=min(W,x2); sy1=min(H,y2)
                dx1=dx0+(sx1-sx0); dy1=dy0+(sy1-sy0)
                patch[:,dy0:dy1,dx0:dx1]=img[:,sy0:sy1,sx0:sx1]
                tiles.append(Tile(data=patch, coords=(x1-left,y1-top), weight=wmap))
        self._pad_h = pad_h; self._pad_w = pad_w
        return tiles

    def stitch(self, sr_tiles: list[np.ndarray], coords: list[tuple[int,int]], out_h: int, out_w: int, scale: int) -> np.ndarray:
        # sr_tiles: list of C x (256*scale) x (256*scale)
        if not sr_tiles: raise ValueError("no tiles")
        C=sr_tiles[0].shape[0]
        acc=np.zeros((C,out_h,out_w), dtype=np.float32)
        wsum=np.zeros((out_h,out_w), dtype=np.float32)
        tile_scaled=self.tile_size*scale
        # weight map scaled
        w=self._weight_map()
        import cv2
        w_scaled=cv2.resize(w, (tile_scaled,tile_scaled), interpolation=cv2.INTER_LINEAR)
        
        for tile, (cx, cy) in zip(sr_tiles, coords):
            x1 = cx * scale
            y1 = cy * scale
            x2 = x1 + tile_scaled
            y2 = y1 + tile_scaled
            
            sx0 = max(0, x1)
            sy0 = max(0, y1)
            sx1 = min(out_w, x2)
            sy1 = min(out_h, y2)
            
            if sx0 >= sx1 or sy0 >= sy1:
                continue
                
            tx0 = sx0 - x1
            ty0 = sy0 - y1
            tx1 = tx0 + (sx1 - sx0)
            ty1 = ty0 + (sy1 - sy0)
            
            w_crop = w_scaled[ty0:ty1, tx0:tx1]
            t_crop = tile[:, ty0:ty1, tx0:tx1]
            
            for c in range(C):
                acc[c, sy0:sy1, sx0:sx1] += t_crop[c] * w_crop
            wsum[sy0:sy1, sx0:sx1] += w_crop
            
        wsum=np.maximum(wsum,1e-6)
        for c in range(C):
            acc[c]/=wsum
        return np.clip(acc,0,255).astype(np.uint8)
