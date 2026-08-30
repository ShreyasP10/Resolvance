from pathlib import Path
import numpy as np
from affine import Affine
from core.config import Settings
from core.pipeline import Pipeline
from core.io import write_geotiff

def test_pipeline_geotiff(tmp_path):
    s=Settings.for_test(tmp_path)
    p=Pipeline(s)
    arr=np.random.randint(0,255,(4,64,64),dtype=np.uint8)
    t=Affine.identity()
    inp=tmp_path/"in.tif"
    write_geotiff(inp, arr, t, "EPSG:32643", t)
    res=p.run(inp, job_id="test123")
    assert res.meta.crs=="EPSG:32643"
    assert "3072" not in res.meta.output_size  # 64*3=192
    assert "192" in res.meta.output_size
    assert res.images.input.startswith("data:image/png")
    assert res.images.heatmap.startswith("data:image/png")
    assert res.download_tif.endswith(".tif")

def test_pipeline_8band_onspot(tmp_path):
    s=Settings.for_test(tmp_path)
    p=Pipeline(s)
    arr=np.random.randint(0,255,(8,64,64),dtype=np.uint8)
    t=Affine.identity()
    inp=tmp_path/"in8.tif"
    write_geotiff(inp, arr, t, "EPSG:32643", t)
    res=p.run(inp, job_id="test8")
    assert "8" in res.meta.input_size  # channel count preserved
