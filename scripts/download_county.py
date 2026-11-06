"""Download independent county footprint evidence with provenance.
Reject truncated service responses rather than treating a partial result as complete."""

import argparse, json, ssl, hashlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request
import certifi
from cmucraft.campus import REGION

SERVICE = (
    "https://gisdata.alleghenycounty.us/arcgis/rest/services/EGIS/Buildings/MapServer/0"
)


def download(output):
    """Fetch the campus county footprint query and retain source provenance."""
    bbox = REGION.download_bbox()
    features = []
    offset = 0
    seen = set()
    while True:
        params = {
            "f": "geojson",
            "where": "1=1",
            "geometry": ",".join(map(str, bbox)),
            "geometryType": "esriGeometryEnvelope",
            "inSR": 4326,
            "outSR": 4326,
            "spatialRel": "esriSpatialRelIntersects",
            "outFields": "OBJECTID",
            "returnGeometry": "true",
            "resultOffset": offset,
            "resultRecordCount": 500,
            "orderByFields": "OBJECTID ASC",
        }
        url = SERVICE + "/query?" + urlencode(params)
        with urlopen(
            Request(url, headers={"User-Agent": "CMUcraft geography audit"}),
            timeout=60,
            context=ssl.create_default_context(cafile=certifi.where()),
        ) as r:
            page = json.load(r)
        if page.get("error") or "features" not in page:
            raise ValueError("County query failed: " + str(page.get("error")))
        rows = page["features"]
        for f in rows:
            oid = f["properties"]["OBJECTID"]
            if oid in seen:
                raise ValueError(
                    "Pagination repeated an object; refusing incomplete data"
                )
            seen.add(oid)
        features.extend(rows)
        offset += len(rows)
        if not rows or len(rows) < 500 and not page.get("exceededTransferLimit"):
            break
    if not features:
        raise ValueError("No independent features returned")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw = json.dumps({"type": "FeatureCollection", "features": features}).encode()
    output.write_bytes(raw)
    meta = {
        "url": SERVICE,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "bbox_wgs84": bbox,
        "features": len(features),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "dataset_observation_date": "not established",
        "license": "Check provider terms before redistributing raw data",
    }
    output.with_suffix(".source.json").write_text(json.dumps(meta, indent=2) + "\n")
    return meta


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument(
        "--output", type=Path, default=Path("build/county-buildings.geojson")
    )
    a = p.parse_args()
    print(json.dumps(download(a.output), indent=2))
