"""Download the recorded official PASDA tile URLs and verify full LAZ streams.
Writes per-file receipts; requires optional survey dependencies and network access."""

import argparse
from cmucraft.lidar import sha256_file
import json
from html.parser import HTMLParser
from pathlib import Path
import urllib.request
import ssl
import certifi

ROOT = Path(__file__).resolve().parents[1]


class Link(HTMLParser):
    """Extract an anchor URL from the tile index HTML field without executing HTML."""

    url = None

    def handle_starttag(self, tag, attrs):
        """Remember the href attribute when a tile download anchor is encountered."""
        if tag == "a":
            self.url = dict(attrs).get("href")


def main():
    """Download missing tiles, decode every point, and save verified download receipts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    args.destination.mkdir(parents=True, exist_ok=True)
    tiles = json.loads(
        (ROOT / "data/reference/survey/pasda-2024-tile-index.json").read_text()
    )
    receipts = []
    for tile in tiles["features"]:
        a = tile["attributes"]
        link = Link()
        link.feed(a["Download"])
        url = link.url
        if not url or not url.startswith(
            "https://www.pasda.psu.edu/download/usgs/PA_17County_2024/"
        ):
            raise ValueError("Unexpected data source")
        target = args.destination / (a["TILEID"] + ".laz")
        if not target.exists():
            temporary = target.with_suffix(".partial")
            with (
                urllib.request.urlopen(
                    url,
                    timeout=180,
                    context=ssl.create_default_context(cafile=certifi.where()),
                ) as source,
                temporary.open("wb") as sink,
            ):
                while chunk := source.read(1024 * 1024):
                    sink.write(chunk)
            temporary.rename(target)
        import laspy

        with laspy.open(target, laz_backend=laspy.LazBackend.Laszip) as reader:
            count = sum(len(p) for p in reader.chunk_iterator(500000))
            if count != reader.header.point_count:
                raise ValueError("Incomplete survey file")
        digest = sha256_file(target)
        receipts.append(
            {"file": target.name, "url": url, "sha256": digest, "points": count}
        )
        print(target.name, count, "points verified", flush=True)
    (args.destination / "download-receipts.json").write_text(
        json.dumps(receipts, indent=2) + "\n"
    )


if __name__ == "__main__":
    main()
