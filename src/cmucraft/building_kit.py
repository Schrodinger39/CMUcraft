"""Coordinate-preserving Builder kits and conservative offline chunk staging.

Never translate mod NBT or edit a live world. Whole reserved chunks (all Y) are
exchanged, including POI; global mod data must be unchanged. Runtime is unverified.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import stat
import struct
import tempfile
import zipfile
import zlib

import nbtlib as n
from PIL import Image, ImageDraw
from shapely.geometry import shape, box

MAX_CHUNK = 64 * 1024 * 1024


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def safe_tree(path):
    path = Path(path)
    if path.is_symlink() or not path.is_dir():
        raise ValueError('Expected a real directory')
    if any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Symlinks are not supported')
    return path


def check_world(path):
    path = safe_tree(path)
    data = n.load(path / 'level.dat')['Data']
    if int(data['DataVersion']) != 2586:
        raise ValueError('Only Java 1.16.5 DataVersion 2586 is supported')
    # Minecraft 1.16 embeds entities in terrain chunks, not a separate store.
    if (path / 'entities').exists():
        raise ValueError('Separate entity storage is unsupported')
    return data


def region_records(folder, rx, rz):
    """Return opaque (compression, payload, timestamp) records, validating allocation."""
    path = Path(folder) / f'r.{rx}.{rz}.mca'
    if not path.exists():
        return {}
    raw = path.read_bytes()
    if not raw:
        # Java may create an empty region file before writing its first record.
        return {}
    if len(raw) < 8192 or len(raw) % 4096:
        raise ValueError('Truncated region')
    used = {0, 1}
    result = {}
    for i in range(1024):
        loc = int.from_bytes(raw[4*i:4*i+4], 'big')
        if not loc:
            continue
        start, count = loc >> 8, loc & 255
        sectors = set(range(start, start + count))
        if not count or start < 2 or (start + count)*4096 > len(raw) or used & sectors:
            raise ValueError('Invalid or overlapping region allocation')
        used |= sectors
        at = start*4096
        length = int.from_bytes(raw[at:at+4], 'big')
        if length < 1 or length + 4 > count*4096:
            raise ValueError('Invalid chunk length')
        compression = raw[at+4]
        cx, cz = rx*32 + i%32, rz*32 + i//32
        if compression & 128:
            if length != 1:
                raise ValueError('Invalid external chunk stub')
            payload = (Path(folder) / f'c.{cx}.{cz}.mcc').read_bytes()
        else:
            payload = raw[at+5:at+4+length]
        compression &= 127
        if compression not in (1, 2, 3) or len(payload) > MAX_CHUNK:
            raise ValueError('Unsupported or oversized chunk')
        result[(cx, cz)] = (compression, payload, raw[4096+4*i:4100+4*i])
    return result


def chunk_nbt(record, cx, cz):
    kind, payload, _ = record
    if kind == 3:
        data = payload
    else:
        decoder = zlib.decompressobj(31 if kind == 1 else 15)
        data = decoder.decompress(payload, MAX_CHUNK + 1)
        if len(data) > MAX_CHUNK or not decoder.eof or decoder.unused_data:
            raise ValueError('Invalid or excessive decompressed chunk')
    obj = n.File.parse(io.BytesIO(data))
    if int(obj['DataVersion']) != 2586:
        raise ValueError('Unexpected chunk DataVersion')
    level = obj['Level']
    if (int(level['xPos']), int(level['zPos'])) != (cx, cz):
        raise ValueError('Chunk coordinate mismatch')
    return obj


def write_region(folder, rx, rz, records):
    """Repack sectors without interpreting or rewriting any NBT payload."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    header, body = bytearray(8192), bytearray()
    sector = 2
    for (cx, cz), (kind, payload, stamp) in sorted(records.items()):
        if (cx//32, cz//32) != (rx, rz):
            raise ValueError('Wrong region coordinates')
        record = struct.pack('>I', len(payload)+1) + bytes([kind]) + payload
        count = math.ceil(len(record)/4096)
        sidecar = folder / f'c.{cx}.{cz}.mcc'
        if count > 255:
            sidecar.write_bytes(payload)
            record = struct.pack('>I', 1) + bytes([kind | 128])
            count = 1
        elif sidecar.exists():
            sidecar.unlink()
        i = cx%32 + 32*(cz%32)
        header[4*i:4*i+4] = ((sector << 8) | count).to_bytes(4, 'big')
        header[4096+4*i:4100+4*i] = stamp
        body.extend(record + bytes(count*4096-len(record)))
        sector += count
    (folder / f'r.{rx}.{rz}.mca').write_bytes(header + body)


def selected(world, chunks, folder='region'):
    records = {}
    for rx, rz in sorted({(x//32, z//32) for x, z in chunks}):
        records.update(region_records(Path(world)/folder, rx, rz))
    return {tuple(c): records.get(tuple(c)) for c in chunks}


def fingerprint(record):
    return None if record is None else digest(bytes([record[0]]) + record[1])


def global_files(world):
    """Require global saved data/config/datapacks/dimensions to remain unchanged.

    Excludes only player/session/UI state and stores handled separately.
    Unknown root files are included so mod-specific storage fails closed.
    """
    ignored = {'region', 'poi', 'playerdata', 'stats', 'advancements',
               'level.dat', 'level.dat_old', 'session.lock', 'icon.png'}
    result = {}
    raid_paths = {'data/raids.dat', 'DIM-1/data/raids.dat', 'DIM1/data/raids_end.dat'}
    for p in sorted(Path(world).rglob('*')):
        if not p.is_file() or p.relative_to(world).parts[0] in ignored:
            continue
        key = p.relative_to(world).as_posix()
        if key == 'xaeromap.txt' and re.fullmatch(r'id:-?\d+\s*', p.read_text()):
            # Per-world client map identity is not building data; retain target ID.
            continue
        if key in raid_paths:
            obj = n.load(p)
            data = obj.get('data', {})
            if (set(obj) == {'data', 'DataVersion'} and int(obj['DataVersion']) == 2586
                    and set(data) == {'Raids', 'NextAvailableID', 'Tick'}
                    and len(data['Raids']) == 0 and int(data['NextAvailableID']) == 1):
                # Only a pristine raid manager's elapsed tick counter is irrelevant.
                # Active/history-bearing/unknown records still compare exact bytes.
                result[key] = 'pristine-raid-manager-2586'
                continue
        result[key] = digest(p.read_bytes())
    return result


def validate_manifest(m):
    if m['schema'] != 1 or m['translation_xyz'] != [0, 0, 0]:
        raise ValueError('Only schema 1, untranslated kits are supported')
    chunks = m['chunks']
    if not chunks or len(chunks) > 256 or len({tuple(c) for c in chunks}) != len(chunks):
        raise ValueError('Invalid chunk reservation')
    if any(len(c) != 2 or any(type(v) is not int or not 0 <= v < 64 for v in c) for c in chunks):
        raise ValueError('Reservation must be inside the 1024 m campus')
    return chunks


def create_kit(root, building, base, output, spawn_y):
    root, base, output = Path(root), Path(base), Path(output)
    if not re.fullmatch(r'[a-z0-9-]+', building):
        raise ValueError('Invalid building ID')
    check_world(base)
    if output.exists() or Path(str(output) + '.zip').exists():
        raise ValueError('Output already exists')
    if base.resolve() == output.resolve() or base.resolve() in output.resolve().parents:
        raise ValueError('Kit output must be outside the base world')
    if not 1 <= spawn_y <= 255:
        raise ValueError('Spawn Y must be 1..255')
    reference = json.loads((root/'data/reference/buildings'/f'{building}.json').read_text())
    campus = json.loads((root/'campus_artifacts/manifest.json').read_text())
    if reference['utm_origin'] != campus['region']['utm_origin']:
        raise ValueError('Reference/campus origin mismatch')
    g = shape(reference['footprint_xz'])
    a, b, c, d = g.bounds
    x0, z0 = math.floor(a/16), math.floor(b/16)
    side = max(math.ceil(c/16)-x0, math.ceil(d/16)-z0)
    chunks = [[x, z] for z in range(z0, z0+side) for x in range(x0, x0+side)]
    m = {'schema': 1, 'building_id': building, 'name': reference['name'],
         'translation_xyz': [0, 0, 0], 'chunks': chunks,
         'bounds_xz_exclusive': [x0*16, z0*16, (x0+side)*16, (z0+side)*16],
         'utm_origin': reference['utm_origin'], 'vertical_offset_m': campus['vertical_offset_m'],
         'reference_sha256': digest((root/'data/reference/buildings'/f'{building}.json').read_bytes()),
         'runtime_verified': False, 'modpack_sha256': digest((root/'modpack/modrinth.index.json').read_bytes())}
    validate_manifest(m)
    terrain = selected(base, chunks)
    if any(r is None for r in terrain.values()):
        raise ValueError('Base is missing reserved chunks')
    for (x, z), record in terrain.items():
        chunk_nbt(record, x, z)
    m['baseline'] = {folder: {f'{x},{z}': fingerprint(r) for (x,z), r in selected(base, chunks, folder).items()}
                     for folder in ('region', 'poi')}
    m['global_files'] = global_files(base)
    m['worldgen_snbt'] = n.load(base/'level.dat')['Data']['WorldGenSettings'].snbt()
    reservation = box(*m['bounds_xz_exclusive'])
    m['intersecting_references'] = [p.stem for p in sorted((root/'data/reference/buildings').glob('*.json'))
        if p.stem != building and shape(json.loads(p.read_text())['footprint_xz']).intersects(reservation)]
    output.mkdir(parents=True)
    # The full base is retained so landmarks/terrain and mod-global state are available.
    shutil.copytree(base, output/'starter-world')
    for name in ('playerdata', 'stats', 'advancements'):
        shutil.rmtree(output/'starter-world'/name, ignore_errors=True)
    for name in ('session.lock', 'level.dat_old'):
        (output/'starter-world'/name).unlink(missing_ok=True)
    level = n.load(output/'starter-world/level.dat')
    data = level['Data']
    data.pop('Player', None)
    data['LevelName'] = n.String('CMUcraft Kit - ' + reference['name'])
    data['SpawnX'], data['SpawnY'], data['SpawnZ'] = n.Int(x0*16+side*8), n.Int(spawn_y), n.Int(z0*16+side*8)
    data['GameType'], data['allowCommands'] = n.Int(1), n.Byte(1)
    data['BorderCenterX'], data['BorderCenterZ'] = n.Double(x0*16+side*8), n.Double(z0*16+side*8)
    data['BorderSize'] = n.Double(side*16)
    data['BorderSizeLerpTarget'] = n.Double(side*16)
    data['BorderSizeLerpTime'] = n.Long(0)
    level.save(output/'starter-world/level.dat')
    write_json(output/'kit.json', m)
    shutil.copy2(root/'modpack/modrinth.index.json', output/'modrinth.index.json')
    shutil.copy2(root/'data/reference/buildings'/f'{building}.json', output/'reference.json')
    for filename in ('DATA_LICENSE.md', 'LICENSE'):
        shutil.copy2(root/filename, output/filename)
    im = Image.new('RGB', (720, 800), 'white')
    draw = ImageDraw.Draw(im)
    scale = 640/(side*16)
    def xy(p):
        return (40+(p[0]-x0*16)*scale, 100+(p[1]-z0*16)*scale)
    draw.text((20,20), reference['name']+' | North up; X east, Z south', fill='black')
    draw.text((20,45), 'Red: full-height reservation; green: source footprint, not surveyed facade', fill='black')
    draw.rectangle((40,100,680,740), outline='red', width=3)
    for poly in (g.geoms if hasattr(g, 'geoms') else [g]):
        draw.polygon([xy(p) for p in poly.exterior.coords], fill='#9fcdb1', outline='black')
        for ring in poly.interiors:
            draw.polygon([xy(p) for p in ring.coords], fill='white', outline='black')
    draw.text((20,760), f'Bounds X/Z: {m["bounds_xz_exclusive"]}; 1 block = 1 metre. (c) OSM contributors', fill='black')
    im.save(output/'footprint.png')
    (output/'START-HERE.md').write_text(f'''# {reference['name']} Building Kit

Experimental kit: Minecraft client behavior has NOT been verified.

1. Ask the maintainer to confirm your claim and the whole red reservation before building.
2. Install the pinned Workbench using the repository launcher guide. No Python or Git needed.
3. Close Minecraft. Copy `starter-world` into that instance's `saves` folder and rename the copy uniquely.
4. Open **CMUcraft Kit - {reference['name']}**. Use F3 for coordinates; north is decreasing Z.
5. Build inside X [{x0*16}, {(x0+side)*16-1}], Z [{z0*16}, {(z0+side)*16-1}], Y [0, 255].
   The world border marks this reservation. Do not move/rotate the world or change the border.
6. Existing buildings are rough context. Agree which existing blocks may be replaced; preserve neighbors and terrain.
7. Save/quit/reopen to check your work. Then fully exit Minecraft and ZIP the entire save folder.
8. Submit the ZIP/link, this kit.json, screenshots, sources and test results using Building submission on GitHub.

All chunks inside the reservation, including terrain and underground blocks, will be replaced together.
Intersecting reference buildings: {', '.join(m['intersecting_references']) or 'none in the 41-record inventory'}.
This inventory is incomplete: the maintainer must also inspect the actual world and active claims.

Spawn: {x0*16+side*8}, {spawn_y}, {z0*16+side*8}; maintainer must check it is safe before distribution.
Translation to campus: (0, 0, 0). Elevation in metres = Minecraft Y + {m['vertical_offset_m']}.
Use `reference.json` for source links, uncertain heights and facade requirements; `footprint.png` for the plan.
Photos are linked, not redistributed. This kit contains no approved facade design or measured height guarantee.

Use full saves for Chisels & Bits, including every .mcc next to .mca. Schematic-only detail submissions are not accepted.
See https://github.com/Schrodinger39/CMUcraft/blob/main/docs/BUILDERS.md for the full instructions.
''', encoding='utf-8')
    shutil.make_archive(str(output), 'zip', output.parent, output.name)
    return m


def plan_import(base, submission, manifest):
    """Fail closed on stale target chunks/global data; produce a reviewable dry run."""
    base, submission = Path(base), Path(submission)
    check_world(base)
    check_world(submission)
    chunks = validate_manifest(manifest)
    for world in (base, submission):
        if n.load(world/'level.dat')['Data']['WorldGenSettings'] != n.parse_nbt(manifest['worldgen_snbt']):
            raise ValueError('World generation settings differ')
        if global_files(world) != manifest['global_files']:
            raise ValueError('Global data/config/dimensions differ; manual compatibility review required')
    changes = []
    for folder in ('region', 'poi'):
        target, source = selected(base, chunks, folder), selected(submission, chunks, folder)
        for (x,z), record in source.items():
            key = f'{x},{z}'
            if fingerprint(target[(x,z)]) != manifest['baseline'][folder][key]:
                raise ValueError(f'Target conflict in {folder} chunk {key}; issue a new kit')
            if folder == 'region':
                if record is None:
                    raise ValueError(f'Submission missing chunk {key}')
                chunk_nbt(record, x, z)
            changes.append({'store': folder, 'chunk': [x,z], 'before': fingerprint(target[(x,z)]), 'after': fingerprint(record)})
    return {'schema': 1, 'building_id': manifest['building_id'],
            'kit_sha256': digest(json.dumps(manifest, sort_keys=True).encode()),
            'changes': changes, 'runtime_verified': False,
            'warning': 'Whole chunks, all Y; entities/ticks included. Staging only, never automatic acceptance.'}


def stage_import(base, submission, manifest, output, approved_plan):
    base, submission, output = Path(base), Path(submission), Path(output)
    # Review must refer to exactly the data that is about to be staged.
    plan = plan_import(base, submission, manifest)
    if approved_plan != plan:
        raise ValueError('Plan changed; rerun dry run and review')
    if output.exists() or any(p.resolve() in output.resolve().parents for p in (base, submission)):
        raise ValueError('Use a new output outside both input worlds')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staging = Path(temp)/'world'
        shutil.copytree(base, staging)
        for folder in ('region', 'poi'):
            replacements = selected(submission, manifest['chunks'], folder)
            for rx, rz in sorted({(x//32,z//32) for x,z in replacements}):
                records = region_records(staging/folder, rx, rz)
                for (x,z), record in replacements.items():
                    if (x//32,z//32) != (rx,rz):
                        continue
                    if record is None:
                        records.pop((x,z), None)
                        (staging/folder/f'c.{x}.{z}.mcc').unlink(missing_ok=True)
                    else:
                        records[(x,z)] = record
                write_region(staging/folder, rx, rz, records)
            actual = selected(staging, manifest['chunks'], folder)
            if any(fingerprint(actual[c]) != fingerprint(r) for c,r in replacements.items()):
                raise ValueError('Staging payload verification failed')
        (staging/'session.lock').unlink(missing_ok=True)
        staging.rename(output)
    return plan


def unpack_submission(archive, output, max_bytes=2 * 1024**3):
    """Extract a ZIP into a new quarantine folder after bounding paths and size.

    This is archive hygiene, not malware or Minecraft command-block scanning.
    """
    output = Path(output)
    if output.exists():
        raise ValueError('Quarantine output already exists')
    with zipfile.ZipFile(archive) as z:
        entries = z.infolist()
        if len(entries) > 20000 or sum(e.file_size for e in entries) > max_bytes:
            raise ValueError('Archive exceeds review limits')
        seen = set()
        for entry in entries:
            name = entry.filename
            parts = name.rstrip('/').split('/')
            mode = entry.external_attr >> 16
            normalized = name.rstrip('/').casefold()
            if (not name or name.startswith('/') or '\\' in name or ':' in name
                    or any(p in ('', '.', '..') for p in parts)
                    or normalized in seen or stat.S_ISLNK(mode)
                    or entry.flag_bits & 1
                    or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))):
                raise ValueError('Unsafe or duplicate ZIP entry')
            seen.add(normalized)
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=output.parent) as temp:
            target = Path(temp)/'unpacked'
            target.mkdir()
            total = 0
            for entry in entries:
                path = target/entry.filename
                if entry.is_dir():
                    path.mkdir(parents=True, exist_ok=True)
                    continue
                path.parent.mkdir(parents=True, exist_ok=True)
                with z.open(entry) as src, path.open('xb') as dst:
                    while block := src.read(1024*1024):
                        total += len(block)
                        if total > max_bytes:
                            raise ValueError('Expanded archive exceeds review limits')
                        dst.write(block)
            target.rename(output)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest='command', required=True)
    unpack = sub.add_parser('unpack')
    unpack.add_argument('archive', type=Path)
    unpack.add_argument('--output', type=Path, required=True)
    make = sub.add_parser('create')
    make.add_argument('building')
    make.add_argument('--root', type=Path, default=Path('.'))
    make.add_argument('--base', type=Path, required=True)
    make.add_argument('--output', type=Path, required=True)
    make.add_argument('--spawn-y', type=int, required=True)
    for name in ('plan', 'stage'):
        cmd = sub.add_parser(name)
        cmd.add_argument('--base', type=Path, required=True)
        cmd.add_argument('--submission', type=Path, required=True)
        cmd.add_argument('--kit', type=Path, required=True)
        cmd.add_argument('--plan', type=Path, required=True)
        if name == 'stage':
            cmd.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.command == 'unpack':
        unpack_submission(a.archive, a.output)
    elif a.command == 'create':
        create_kit(a.root, a.building, a.base, a.output, a.spawn_y)
    else:
        m = json.loads(a.kit.read_text())
        if a.command == 'plan':
            if a.plan.exists():
                raise ValueError('Plan output already exists')
            write_json(a.plan, plan_import(a.base, a.submission, m))
        else:
            stage_import(a.base, a.submission, m, a.output, json.loads(a.plan.read_text()))


if __name__ == '__main__':
    main()
