from pathlib import Path
import numpy as np, tifffile
from affine import Affine
from core.io import read_geotiff, write_geotiff, normalize_to_uint8_per_band

def test_nband_roundtrip(tmp_path):
    arr=np.random.randint(0,255,(4,64,64),dtype=np.uint8)
    p=tmp_path/"in.tif"
    t=Affine.scale(10,-10)*Affine.translation(0,0)
    write_geotiff(p, arr, t, "EPSG:32643", t)
    geo=read_geotiff(p)
    assert geo.count==4
    assert geo.band.shape[0]==4
    assert str(geo.crs)=="EPSG:32643"
    # transform scaled
    new_t=t*Affine.scale(1/3,1/3)
    out=tmp_path/"out.tif"
    write_geotiff(out, np.repeat(arr,3,axis=1).repeat(3,axis=2)[:,:192,:192], t, geo.crs, new_t)
    geo2=read_geotiff(out)
    assert geo2.width==192

def test_per_band_normalize():
    arr=np.random.randint(0,1000,(4,32,32)).astype(float)
    out=normalize_to_uint8_per_band(arr)
    assert out.shape==arr.shape
    assert out.dtype==np.uint8
