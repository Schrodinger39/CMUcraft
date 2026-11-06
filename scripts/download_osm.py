#!/usr/bin/env python3
"""Run from an installed checkout: python scripts/download_osm.py."""
from cmucraft.geo import Region
from cmucraft.osm import download
if __name__ == '__main__':
    print(download(Region(),'data/raw/cmu.osm'))
