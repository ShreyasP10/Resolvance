from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Optional

class FileType(str, Enum):
    GEOTIFF = "GeoTIFF"
    IMAGE = "Image"

@dataclass
class ImageSet:
    input: str
    sr: str
    heatmap: str

@dataclass
class JobMeta:
    job_id: str
    input_size: str
    output_size: str
    crs: str
    elapsed: float
    file_type: FileType

@dataclass
class InferenceResult:
    job_id: str
    images: ImageSet
    download_png: str
    download_tif: Optional[str]
    download_heatmap: Optional[str]
    meta: JobMeta
    metrics: Optional[dict]

    def to_dict(self):
        return {
            "success": True,
            "images": {
                "input": self.images.input,
                "sr": self.images.sr,
                "heatmap": self.images.heatmap,
            },
            "download": self.download_png,
            "download_tif": self.download_tif,
            "download_heatmap": self.download_heatmap,
            "meta": {
                "job_id": self.meta.job_id,
                "input_size": self.meta.input_size,
                "output_size": self.meta.output_size,
                "crs": self.meta.crs,
                "elapsed": str(self.meta.elapsed),
                "file_type": self.meta.file_type.value,
            },
            "metrics": self.metrics or {},
        }
