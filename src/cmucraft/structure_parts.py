"""Preserve elevated connector geometry separately from ground-supported buildings."""
import xml.etree.ElementTree as ET
from shapely.geometry import Polygon
from .osm import parse

GATES_HILLMAN_PARENT='21724638'


def campus_parts(path):
    buildings,warnings=parse(path,separate_named_parts=True)
    if warnings:raise ValueError(warnings)
    root=ET.parse(path).getroot()
    nodes={n.attrib['id']:(float(n.attrib['lon']),float(n.attrib['lat'])) for n in root.findall('node')}
    ways={w.attrib['id']:w for w in root.findall('way')}
    parents={r.attrib['id']:r for r in root.findall('relation')}
    connectors=[]
    parent=parents.get(GATES_HILLMAN_PARENT)
    if parent is not None:
        for member in parent.findall('member'):
            if member.attrib['type']!='way':continue
            way=ways[member.attrib['ref']];tags={t.attrib['k']:t.attrib['v'] for t in way.findall('tag')}
            if tags.get('man_made')!='bridge':continue
            coordinates=[nodes[n.attrib['ref']] for n in way.findall('nd')]
            if len(coordinates)<4 or coordinates[0]!=coordinates[-1]:raise ValueError('Unclosed connector')
            geometry=Polygon(coordinates)
            if not geometry.is_valid:raise ValueError('Invalid connector geometry')
            connectors.append({'id':'way/'+way.attrib['id'],'parent_id':'relation/'+GATES_HILLMAN_PARENT,
                'geometry':geometry,'tags':tags,'role':'elevated_connector',
                'deck_elevation_m':None,'ground_extrusion_allowed':False})
    return buildings,connectors
