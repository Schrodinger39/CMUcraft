"""OSM XML download and strict ways/multipolygon assembly, without OSMnx."""
import hashlib
import json
import ssl
import certifi
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from shapely.geometry import Polygon, LineString
from shapely.ops import polygonize_full, unary_union


def download(region, output, endpoint="https://api.openstreetmap.org/api/0.6/map"):
    output = Path(output)
    bbox = region.download_bbox()
    url = endpoint + "?bbox=" + ",".join(f"{v:.8f}" for v in bbox)
    request = urllib.request.Request(url,headers={"User-Agent":"CMUcraft/0.1 educational footprint project"})
    with urllib.request.urlopen(request,timeout=60,context=ssl.create_default_context(cafile=certifi.where())) as response:
        raw = response.read()
    root = ET.fromstring(raw)
    if root.tag != "osm" or not root.findall("way"):
        raise ValueError("Response is not a usable OSM map; refusing to save")
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_bytes(raw)
    meta = {"source_kind":"real_osm", "url":url,"bbox_wgs84":bbox,
            "retrieved_utc":datetime.now(timezone.utc).isoformat(),
            "sha256":hashlib.sha256(raw).hexdigest(),
            "attribution":"© OpenStreetMap contributors", "license":"ODbL 1.0",
            "license_url":"https://www.openstreetmap.org/copyright"}
    output.with_suffix(".source.json").write_text(json.dumps(meta,indent=2)+"\n")
    return meta


def parse(path, separate_named_parts=False):
    root = ET.parse(path).getroot()
    if root.tag != "osm":
        raise ValueError("Expected OSM XML")
    nodes = {n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    ways = {w.attrib['id']:w for w in root.findall('way')}
    tags = lambda el: {t.attrib['k']:t.attrib['v'] for t in el.findall('tag')}
    features, warnings, consumed = [], [], set()

    def coordinates(w):
        return [nodes[n.attrib['ref']] for n in w.findall('nd')]

    def rings(members):
        closed, lines = [], []
        for m in members:
            pts=coordinates(ways[m.attrib['ref']])
            if len(pts)>=4 and pts[0]==pts[-1]:
                polygon=Polygon(pts)
                if not polygon.is_valid:
                    raise ValueError("invalid closed member")
                closed.append(polygon)
            else:
                lines.append(LineString(pts))
        if lines:
            polys,cuts,dangles,invalid = polygonize_full(lines)
            if any(not g.is_empty for g in (cuts,dangles,invalid)):
                raise ValueError("unclosed/incomplete multipolygon ring")
            closed.extend(polys.geoms)
        return closed

    def add(el, geometry, kind):
        if geometry.is_empty or not geometry.is_valid or geometry.geom_type not in ('Polygon','MultiPolygon'):
            raise ValueError("invalid polygon; not silently repaired")
        features.append({"id":f"{kind}/{el.attrib['id']}","tags":tags(el),"geometry":geometry})

    relations = {r.attrib['id']:r for r in root.findall('relation')}
    cache = {}

    def relation_geometry(rid, active=()):
        if rid in active:
            raise ValueError("cyclic relation membership")
        if rid in cache:
            return cache[rid]
        rel = relations[rid]
        if tags(rel).get('type') != 'multipolygon':
            raise ValueError("unsupported building relation type")
        outer_parts, inner_parts, descendants = [], [], set()
        members = rel.findall('member')
        for role, target in [('outer',outer_parts),('inner',inner_parts)]:
            selected = [m for m in members if (m.attrib.get('role') or 'outer') == role]
            target.extend(rings([m for m in selected if m.attrib['type']=='way']))
            for m in selected:
                mid=m.attrib['ref']; kind=m.attrib['type']
                if kind=='relation':
                    child, child_ids = relation_geometry(mid,active+(rid,))
                    target.append(child); descendants.update(child_ids)
                elif kind!='way':
                    raise ValueError("unsupported multipolygon member")
                descendants.add(f"{kind}/{mid}")
        if any((m.attrib.get('role') or 'outer') not in ('outer','inner') for m in members):
            raise ValueError("unsupported member role")
        outer,inner=unary_union(outer_parts),unary_union(inner_parts)
        if not inner.is_empty and not outer.covers(inner):
            raise ValueError("inner rings outside outer rings")
        geometry=outer.difference(inner)
        cache[rid]=(geometry,descendants)
        return geometry,descendants

    for rid,rel in relations.items():
        # Gates/Hillman parent combines separate named buildings and a skybridge.
        # Retain child geometry for architecture; preserve parent for legacy 2D surveys.
        if separate_named_parts and rid == '21724638':
            continue
        if tags(rel).get('building','no') == 'no':
            continue
        try:
            geometry,descendants=relation_geometry(rid)
            add(rel,geometry,'relation')
            consumed.update(descendants)
        except (KeyError,ValueError) as exc:
            warnings.append(f"relation/{rid}: {exc}")
    # Keep complete parent complexes instead of duplicate child footprints.
    features = [f for f in features if f['id'] not in consumed]
    for wid,w in ways.items():
        if f'way/{wid}' in consumed or tags(w).get('building','no') == 'no':
            continue
        try:
            pts = coordinates(w)
            if len(pts)<4 or pts[0] != pts[-1]:
                raise ValueError("building way is not a closed ring")
            add(w,Polygon(pts),'way')
        except (KeyError,ValueError) as exc:
            warnings.append(f"way/{wid}: {exc}")
    return sorted(features,key=lambda f:f['id']),warnings
