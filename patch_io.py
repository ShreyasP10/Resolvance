import re
with open('core/io.py', 'r', encoding='utf-8') as f:
    code = f.read()

old = '''        with tifffile.TiffFile(str(path)) as tif:
            page = tif.pages[0]
            raw = tif.asarray()  # full stack: handles multi-page planar (4,64,64)'''

new = '''        with tifffile.TiffFile(str(path)) as tif:
            page = tif.pages[0]
            # Defense against GeoTIFF decompression bombs
            if page.imagewidth * page.imagelength > 25000000:
                raise DecodingError("Image dimensions too large. Max 25 million pixels (5000x5000) allowed to prevent OOM.")
            raw = tif.asarray()  # full stack: handles multi-page planar (4,64,64)'''

code = code.replace(old, new)

with open('core/io.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Decompression bomb guard added!')
