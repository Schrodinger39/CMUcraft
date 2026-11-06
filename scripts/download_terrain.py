#!/usr/bin/env python3
"""Refresh the fixed campus USGS 3DEP raster; retains HTTPS verification."""
from pathlib import Path
import certifi
import ssl
import urllib.request
from PIL import Image
import hashlib,json
from datetime import datetime,timezone

if __name__=='__main__':
    source=Path('data/raw/terrain.source.json')
    metadata=json.loads(source.read_text())
    request=urllib.request.Request(metadata['source_url'],headers={'User-Agent':'CMUcraft/0.2'})
    with urllib.request.urlopen(request,timeout=90,context=ssl.create_default_context(cafile=certifi.where())) as response:
        raw=response.read()
    import io
    im=Image.open(io.BytesIO(raw))
    if im.size!=(256,256) or im.mode!='F':raise ValueError('Unexpected DEM format')
    Path('data/raw/terrain.tif').write_bytes(raw)
    metadata['sha256']=hashlib.sha256(raw).hexdigest()
    metadata['retrieved_utc']=datetime.now(timezone.utc).isoformat()
    source.write_text(json.dumps(metadata,indent=2)+'\n')
    print('Saved real USGS terrain and provenance')
