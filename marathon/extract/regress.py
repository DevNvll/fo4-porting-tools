#!/usr/bin/env python3
"""Make the extraction of each weapon again and compare the bytes with the stored results.

    ./port marathon regress [NAME ...] [--keep]
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/regress.py [NAME ...] [--keep]

For each folder NAME of data/marathon/extract/out (a result of m2x_extract.py), the program
runs m2x_extract.py again into the scratch folder data/marathon/extract/work/_regress/out and
compares each file (sha256): the manifest, states.json, each .glb file, each texture, each raw
tag. It prints one line for each weapon. For a weapon with a difference it prints one more
line (with two spaces at its start) for each file that is different, with what is different in
it. The exit code is 1 when a file is different, missing or new, or when an extraction fails.

The arguments of an extraction come from the stored manifest: the item hash, the hash of the
art item (`--art`), the number of the arm entity (`--arms`) and the name of the hands file
(`--hands`; the program looks for a file with that name below data/destiny/port/extract and
data/destiny/extract/out, or in the folder of `--hands-folder`). The manifest does not record
`--stages` and `--all-detail`: a result that was made with one of them shows a difference.

A scratch result that is equal is deleted (`--keep` keeps it). A scratch result with a
difference stays, and the log of each extraction is data/marathon/extract/work/_regress/NAME.log.
"""
import argparse
import glob
import hashlib
import importlib.util
import json
import os
import shutil
import struct
import subprocess
import sys

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = paths.data('marathon', 'extract', 'out')
SCRATCH = paths.data('marathon', 'extract', 'work', '_regress')


def digest(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def files_of(folder):
    """{path from the folder: sha256} of each file below a folder."""
    out = {}
    for base, _, names in os.walk(folder):
        for name in names:
            path = os.path.join(base, name)
            out[os.path.relpath(path, folder)] = digest(path)
    return out


def arguments_of(manifest, hands_folders):
    """The arguments of m2x_extract.py that made a manifest, or a text that says why they are not known."""
    args = [manifest['item_hash']]
    if manifest.get('art_item_hash') and manifest['art_item_hash'] != manifest['item_hash']:
        args += ['--art', manifest['art_item_hash']]
    first = manifest.get('first_person') or []
    if not first:
        if manifest.get('arm_entities'):
            args.append('--no-first-person')
        return args
    numbers = [row['number'] for row in manifest.get('arm_entities', [])
               if row['entity'] == first[0]['entity'] and row['name'] == first[0].get('source_name', row['name'])]
    if numbers and numbers[0]:
        args += ['--arms', str(numbers[0])]
    for body in first[0].get('body', []):
        found = sorted(path for folder in hands_folders for path in
                       glob.glob(os.path.join(folder, '**', body['file']), recursive=True))
        if not found:
            return 'the hands file %s is not below %s (give its folder with --hands-folder)' % (body['file'], ' or '.join(hands_folders))
        args += ['--hands', found[0]]
    return args


def glb_chunks(path):
    with open(path, 'rb') as f:
        data = f.read()
    chunks, offset = [], 12
    while offset + 8 <= len(data):
        size, kind = struct.unpack_from('<II', data, offset)
        chunks.append(data[offset + 8:offset + 8 + size])
        offset += 8 + size
    return chunks


def json_differences(a, b, at=''):
    """The places (keys) where two JSON values are different; 12 at most."""
    if type(a) is not type(b):
        return [at or '(top)']
    if isinstance(a, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            out += json_differences(a[key], b[key], '%s.%s' % (at, key) if at else key) if key in a and key in b else ['%s.%s' % (at, key) if at else key]
        return out[:12]
    if isinstance(a, list):
        if len(a) != len(b):
            return ['%s (%d and %d items)' % (at, len(a), len(b))]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += json_differences(x, y, '%s[%d]' % (at, i))
        return out[:12]
    return [] if a == b else [at or '(top)']


def what_differs(old, new):
    """A short text about the difference of two files with other bytes."""
    sizes = '%d and %d bytes' % (os.path.getsize(old), os.path.getsize(new))
    try:
        if old.endswith('.json'):
            with open(old) as f, open(new) as g:
                places = json_differences(json.load(f), json.load(g))
            return 'the values are equal (other text)' if not places else 'different at: ' + ', '.join(places)
        if old.endswith('.png'):
            import numpy as np
            from PIL import Image
            a, b = np.asarray(Image.open(old)), np.asarray(Image.open(new))
            if a.shape != b.shape:
                return 'another picture size: %s and %s' % (a.shape, b.shape)
            count = int((a != b).any(axis=-1).sum()) if a.ndim == 3 else int((a != b).sum())
            return 'the pixels are equal (other bytes of the PNG file; %s)' % sizes if count == 0 else '%d pixels are different' % count
        if old.endswith('.glb'):
            a, b = glb_chunks(old), glb_chunks(new)
            parts = []
            if a[:1] != b[:1]:
                places = json_differences(json.loads(a[0]), json.loads(b[0])) if a and b else []
                parts.append('the JSON part (%s)' % (', '.join(places) or 'other text'))
            if a[1:] != b[1:]:
                parts.append('the binary part (%d and %d bytes)' % (sum(map(len, a[1:])), sum(map(len, b[1:]))))
            return 'different: ' + ' and '.join(parts)
    except Exception as error:      # the hint is not necessary for the result
        return '%s (no more detail: %s)' % (sizes, error)
    return sizes


def main():
    ap = argparse.ArgumentParser(description='Make the extraction of each weapon of data/marathon/extract/out again and compare the bytes. Exit code 1: a difference.')
    ap.add_argument('names', nargs='*', help='the folders of data/marathon/extract/out to do (default: each one with a manifest.json)')
    ap.add_argument('--keep', action='store_true', help='keep the scratch result of a weapon with no difference')
    ap.add_argument('--hands-folder', action='append', default=[], help='a folder with the hands file of a result (more than one is possible)')
    a = ap.parse_args()
    names = a.names or sorted(n for n in (os.listdir(OUT) if os.path.isdir(OUT) else []) if os.path.isfile(os.path.join(OUT, n, 'manifest.json')))
    if not names:
        print('regress: %s has no result of m2x_extract.py: nothing to compare.' % OUT)
        return 0
    hands_folders = a.hands_folder + [paths.data('destiny', 'port', 'extract'), paths.data('destiny', 'extract', 'out')]
    scratch = os.path.join(SCRATCH, 'out')
    os.makedirs(scratch, exist_ok=True)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    # the extraction needs the Python of the environment of d2x; this program needs no module of it
    python, d2x_python = sys.executable, paths.data('destiny', 'extract', 'venv', 'bin', 'python')
    if importlib.util.find_spec('texture2ddecoder') is None and os.path.isfile(d2x_python):
        python = d2x_python
    env['PYTHONPATH'] = os.pathsep.join([paths.repo('destiny', 'extract')] + ([env['PYTHONPATH']] if env.get('PYTHONPATH') else []))
    failed = 0
    for name in names:
        stored = os.path.join(OUT, name)
        if not os.path.isfile(os.path.join(stored, 'manifest.json')):
            print('%s: FAILED: %s has no manifest.json' % (name, stored))
            failed += 1
            continue
        with open(os.path.join(stored, 'manifest.json')) as f:
            args = arguments_of(json.load(f), hands_folders)
        if isinstance(args, str):
            print('%s: FAILED: %s' % (name, args))
            failed += 1
            continue
        new = os.path.join(scratch, name)
        shutil.rmtree(new, ignore_errors=True)
        log = os.path.join(SCRATCH, name + '.log')
        command = [python, os.path.join(HERE, 'm2x_extract.py')] + args + ['--out', scratch]
        with open(log, 'w') as f:
            f.write('$ %s\n' % ' '.join(command))
            f.flush()
            result = subprocess.run(command, env=env, stdin=subprocess.DEVNULL, stdout=f, stderr=subprocess.STDOUT)
        if result.returncode or not os.path.isdir(new):
            print('%s: FAILED: the extraction stopped with the exit code %d, or its folder has another name (log: %s)' % (name, result.returncode, log))
            failed += 1
            continue
        before, after = files_of(stored), files_of(new)
        different = sorted(p for p in before if p in after and before[p] != after[p])
        gone = sorted(p for p in before if p not in after)
        added = sorted(p for p in after if p not in before)
        size = sum(os.path.getsize(os.path.join(stored, p)) for p in before)
        if not different and not gone and not added:
            print('%s: same (%d files, %d bytes)' % (name, len(before), size))
            if not a.keep:
                shutil.rmtree(new, ignore_errors=True)
            continue
        failed += 1
        print('%s: DIFFERENT: %d of %d files have other bytes; %d files are not in the new result; %d files are not in the stored result (scratch result: %s)' % (
            name, len(different), len(before), len(gone), len(added), new))
        for p in different:
            print('  %s: %s' % (p, what_differs(os.path.join(stored, p), os.path.join(new, p))))
        for p in gone:
            print('  %s: not in the new result' % p)
        for p in added:
            print('  %s: not in the stored result' % p)
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
