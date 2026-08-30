import numpy as np
from core.patch import TileManager

def test_tile_stitch_rmse():
    tm=TileManager(256,16)
    arr=np.random.randint(0,255,(4,512,512),dtype=np.uint8)
    tiles=tm.tile(arr)
    # mock sr: bicubic 3x not needed, just stitch identity scaled
    # Use same arr repeated: stitch with scale 1 should be close
    tm1=TileManager(256,16)
    # create sr tiles as tiled data itself
    sr_tiles=[t.data for t in tiles]
    coords=[t.coords for t in tiles]
    stitched=tm1.stitch(sr_tiles, coords, 512,512, scale=1)
    rmse=np.sqrt(np.mean((stitched.astype(float)-arr.astype(float))**2))
    assert rmse < 1.0

def test_8band():
    tm=TileManager(256,16)
    arr=np.random.randint(0,255,(8,300,300),dtype=np.uint8)
    tiles=tm.tile(arr)
    assert len(tiles)>0
    sr_tiles=[t.data for t in tiles]
    coords=[t.coords for t in tiles]
    stitched=tm.stitch(sr_tiles, coords, 300,300,1)
    assert stitched.shape==(8,300,300)
