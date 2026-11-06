#!/usr/bin/env python3
"""Convenience script for the original OSM download.
The shared downloader records real source bytes and provenance; failures are explicit.
"""

from cmucraft.geo import Region
from cmucraft.osm import download

if __name__ == "__main__":
    print(download(Region(), "data/raw/cmu.osm"))
