"""Read a Gamebryo file of Fallout 3 and Fallout: New Vegas (NIF or KF, version 20.2.0.7).

    python3 tools/fnvnif.py FILE.nif            the nodes and the shapes
    python3 tools/fnvnif.py FILE.kf             the sequence, its tracks and its text keys

The header has the size of each block, so a block type that is not here is skipped.
A transform is a translation (x, y, z), a rotation matrix (3 rows, column vectors) and a scale.
"""
import struct
import sys
import numpy as np

FLT_LIMIT = 1e20          # the file has -3.4e38 for "no value"


class Reader:
    def __init__(self, data, pos, strings):
        self.d, self.p, self.strings = data, pos, strings

    def u8(self):
        v = self.d[self.p]; self.p += 1; return v

    def u16(self):
        v, = struct.unpack_from('<H', self.d, self.p); self.p += 2; return v

    def i32(self):
        v, = struct.unpack_from('<i', self.d, self.p); self.p += 4; return v

    def u32(self):
        v, = struct.unpack_from('<I', self.d, self.p); self.p += 4; return v

    def f32(self):
        v, = struct.unpack_from('<f', self.d, self.p); self.p += 4; return v

    def floats(self, n):
        v = np.frombuffer(self.d, '<f4', n, self.p).astype(np.float64); self.p += 4 * n; return v

    def u16s(self, n):
        v = np.frombuffer(self.d, '<u2', n, self.p).astype(np.int64); self.p += 2 * n; return v

    def string(self):
        i = self.i32()
        return self.strings[i] if 0 <= i < len(self.strings) else None

    def sized(self):
        n = self.u32(); s = self.d[self.p:self.p + n]; self.p += n; return s.decode('latin1')

    def refs(self):
        n = self.u32()
        return [self.i32() for _ in range(n)]


class Nif:
    def __init__(self, path):
        d = open(path, 'rb').read()
        self.path = path
        e = d.index(b'\n')
        self.header_line = d[:e].decode('latin1')
        p = e + 1
        self.version, endian, self.user, nblocks, self.user2 = struct.unpack_from('<IBIII', d, p)
        p += 17
        if self.version != 0x14020007 or endian != 1:
            raise ValueError('%s: not a little-endian 20.2.0.7 file' % path)
        for _ in range(3):
            p += 1 + d[p]
        nt, = struct.unpack_from('<H', d, p); p += 2
        types = []
        for _ in range(nt):
            n, = struct.unpack_from('<I', d, p); p += 4
            types.append(d[p:p + n].decode('latin1')); p += n
        idx = struct.unpack_from('<%dH' % nblocks, d, p); p += 2 * nblocks
        self.sizes = struct.unpack_from('<%dI' % nblocks, d, p); p += 4 * nblocks
        ns, _ = struct.unpack_from('<II', d, p); p += 8
        self.strings = []
        for _ in range(ns):
            n, = struct.unpack_from('<I', d, p); p += 4
            self.strings.append(d[p:p + n].decode('latin1')); p += n
        ng, = struct.unpack_from('<I', d, p); p += 4 + 4 * ng
        self.types = [types[i] for i in idx]
        self.offsets = []
        for s in self.sizes:
            self.offsets.append(p); p += s
        self.data = d
        self.blocks = [None] * nblocks
        self.problems = []
        for i in range(nblocks):
            fn = getattr(self, '_' + self.types[i], None)
            if fn is None:
                continue
            r = Reader(d, self.offsets[i], self.strings)
            b = fn(r)
            b['type'] = self.types[i]
            b['index'] = i
            used = r.p - self.offsets[i]
            if used != self.sizes[i]:
                self.problems.append('%s %d: read %d of %d bytes' % (self.types[i], i, used, self.sizes[i]))
            self.blocks[i] = b
        if self.problems:
            raise ValueError('%s: %s' % (path, '; '.join(self.problems[:5])))

    # ---- objects
    def _objectnet(self, r):
        return {'name': r.string(), 'extra': r.refs(), 'controller': r.i32()}

    def _avobject(self, r):
        b = self._objectnet(r)
        b['flags'] = r.u32()
        b['translation'] = r.floats(3)
        b['rotation'] = r.floats(9).reshape(3, 3)
        b['scale'] = r.f32()
        b['properties'] = r.refs()
        b['collision'] = r.i32()
        return b

    def _NiNode(self, r):
        b = self._avobject(r)
        b['children'] = r.refs()
        b['effects'] = r.refs()
        return b

    _BSFadeNode = _NiNode

    def _geometry(self, r):
        b = self._avobject(r)
        b['data'] = r.i32()
        b['skin'] = r.i32()
        n = r.u32()
        b['material_names'] = [(r.string(), r.i32()) for _ in range(n)]
        b['active_material'] = r.i32()
        b['dirty'] = r.u8()
        return b

    _NiTriStrips = _geometry
    _NiTriShape = _geometry

    def _geomdata(self, r):
        b = {'group': r.i32()}
        n = b['num_vertices'] = r.u16()
        b['keep'], b['compress'] = r.u8(), r.u8()
        b['vertices'] = r.floats(3 * n).reshape(n, 3) if r.u8() else None
        flags = b['vector_flags'] = r.u16()
        has_normals = r.u8()
        b['normals'] = r.floats(3 * n).reshape(n, 3) if has_normals else None
        if has_normals and flags & 0x1000:
            b['tangents'] = r.floats(3 * n).reshape(n, 3)
            b['bitangents'] = r.floats(3 * n).reshape(n, 3)
        b['center'], b['radius'] = r.floats(3), r.f32()
        b['colors'] = r.floats(4 * n).reshape(n, 4) if r.u8() else None
        b['uv'] = [r.floats(2 * n).reshape(n, 2) for _ in range(flags & 0x3F)]
        b['consistency'] = r.u16()
        b['additional'] = r.i32()
        return b

    def _NiTriStripsData(self, r):
        b = self._geomdata(r)
        b['num_triangles'] = r.u16()
        ns = r.u16()
        lengths = [r.u16() for _ in range(ns)]
        tris = []
        if r.u8():
            for ln in lengths:
                s = r.u16s(ln)
                for k in range(ln - 2):
                    a, c, e = int(s[k]), int(s[k + 1]), int(s[k + 2])
                    if a == c or c == e or a == e:
                        continue
                    tris.append((a, c, e) if k % 2 == 0 else (a, e, c))
        b['triangles'] = np.array(tris, np.int64).reshape(-1, 3)
        return b

    def _NiTriShapeData(self, r):
        b = self._geomdata(r)
        nt = b['num_triangles'] = r.u16()
        r.u32()
        b['triangles'] = r.u16s(3 * nt).reshape(nt, 3) if r.u8() else np.zeros((0, 3), np.int64)
        for _ in range(r.u16()):
            r.p += 2 * r.u16()
        return b

    def _BSShaderPPLightingProperty(self, r):
        b = self._objectnet(r)
        b['flags'] = r.u16()
        b['shader_type'], b['shader_flags'], b['shader_flags2'] = r.u32(), r.u32(), r.u32()
        b['env_scale'] = r.f32()
        b['clamp'] = r.u32()
        b['texture_set'] = r.i32()
        b['refraction'], b['refraction_period'] = r.f32(), r.i32()
        b['parallax_passes'], b['parallax_scale'] = r.f32(), r.f32()
        return b

    def _BSShaderTextureSet(self, r):
        return {'textures': [r.sized() for _ in range(r.i32())]}

    def _NiMaterialProperty(self, r):
        b = self._objectnet(r)
        b['specular'], b['emissive'] = r.floats(3), r.floats(3)
        b['glossiness'], b['alpha'], b['emissive_mult'] = r.f32(), r.f32(), r.f32()
        return b

    def _NiAlphaProperty(self, r):
        b = self._objectnet(r)
        b['flags'], b['threshold'] = r.u16(), r.u8()
        return b

    def _NiStringExtraData(self, r):
        return {'name': r.string(), 'value': r.string()}

    # ---- animation
    def _NiControllerSequence(self, r):
        b = {'name': r.string()}
        n = r.u32()
        r.u32()
        tracks = []
        for _ in range(n):
            t = {'interpolator': r.i32(), 'controller': r.i32(), 'priority': r.u8()}
            t['node'], t['property'], t['controller_type'], t['variable1'], t['variable2'] = [r.string() for _ in range(5)]
            tracks.append(t)
        b['tracks'] = tracks
        b['weight'] = r.f32()
        b['text_keys'] = r.i32()
        b['cycle'], b['frequency'] = r.u32(), r.f32()
        b['start'], b['stop'] = r.f32(), r.f32()
        b['manager'] = r.i32()
        b['accum_root'] = r.string()
        b['notes'] = [r.i32() for _ in range(r.u16())]
        return b

    def _NiTextKeyExtraData(self, r):
        b = {'name': r.string()}
        b['keys'] = [(r.f32(), r.string()) for _ in range(r.u32())]
        return b

    def _NiTransformInterpolator(self, r):
        return {'translation': r.floats(3), 'rotation': r.floats(4), 'scale': r.f32(), 'data': r.i32()}

    def _keys(self, r, width):
        """A key group: the interpolation type and the keys (time, value, forward, backward)."""
        n = r.u32()
        if n == 0:
            return {'type': 0, 'keys': []}
        kind = r.u32()
        keys = []
        for _ in range(n):
            k = {'time': r.f32(), 'value': r.floats(width) if width > 1 else r.f32()}
            if kind == 2:
                k['forward'] = r.floats(width) if width > 1 else r.f32()
                k['backward'] = r.floats(width) if width > 1 else r.f32()
            elif kind == 3:
                k['tbc'] = r.floats(3)
            elif kind not in (1, 5):
                raise ValueError('key type %d' % kind)
            keys.append(k)
        return {'type': kind, 'keys': keys}

    def _NiTransformData(self, r):
        b = {}
        n = r.u32()
        b['rotations'] = {'type': 0, 'keys': []}
        b['euler'] = None
        if n:
            kind = r.u32()
            if kind == 4:
                b['euler'] = [self._keys(r, 1) for _ in range(3)]
                b['rotations'] = {'type': 4, 'keys': []}
            else:
                keys = []
                for _ in range(n):
                    k = {'time': r.f32(), 'value': r.floats(4)}        # w, x, y, z
                    if kind == 3:
                        k['tbc'] = r.floats(3)
                    keys.append(k)
                b['rotations'] = {'type': kind, 'keys': keys}
        b['translations'] = self._keys(r, 3)
        b['scales'] = self._keys(r, 1)
        return b

    # ---- views
    def root(self):
        for b in self.blocks:
            if b is not None and b['type'] in ('NiNode', 'BSFadeNode'):
                return b
        return None

    def walk(self):
        """Each node and shape below the root: (block, parent block, world rotation, world translation, world scale)."""
        out = []

        def visit(b, parent, rot, tr, sc):
            wr = rot @ b['rotation']
            wt = tr + sc * (rot @ b['translation'])
            ws = sc * b['scale']
            out.append((b, parent, wr, wt, ws))
            for c in b.get('children', []):
                if c >= 0 and self.blocks[c] is not None and 'translation' in self.blocks[c]:
                    visit(self.blocks[c], b, wr, wt, ws)
        visit(self.root(), None, np.eye(3), np.zeros(3), 1.0)
        return out

    def textures(self, shape):
        for p in shape['properties']:
            b = self.blocks[p] if p >= 0 else None
            if b is not None and b['type'] == 'BSShaderPPLightingProperty' and b['texture_set'] >= 0:
                return self.blocks[b['texture_set']]['textures']
        return []

    def sequence(self):
        for b in self.blocks:
            if b is not None and b['type'] == 'NiControllerSequence':
                return b
        return None


def main(path):
    nif = Nif(path)
    seq = nif.sequence()
    if seq is not None:
        print('sequence', seq['name'], 'start', seq['start'], 'stop', seq['stop'], 'cycle', seq['cycle'], 'frequency', seq['frequency'],
              'accum', seq['accum_root'], 'tracks', len(seq['tracks']))
        tk = nif.blocks[seq['text_keys']] if seq['text_keys'] >= 0 else None
        if tk:
            for t, s in tk['keys']:
                print('  text key %.4f %r' % (t, s))
        for t in seq['tracks']:
            ip = nif.blocks[t['interpolator']]
            d = nif.blocks[ip['data']] if ip and ip['data'] >= 0 else None
            nr = len(d['rotations']['keys']) if d else 0
            ne = [len(g['keys']) for g in d['euler']] if d and d['euler'] else None
            print('  %-28s prio %3d %-22s rot type %s keys %s euler %s | tr type %s keys %s | sc keys %s' % (
                t['node'], t['priority'], t['controller_type'], d['rotations']['type'] if d else '-', nr, ne,
                d['translations']['type'] if d else '-', len(d['translations']['keys']) if d else 0, len(d['scales']['keys']) if d else 0))
        return
    for b, parent, wr, wt, ws in nif.walk():
        kind = b['type']
        line = '%-12s %-28s parent %-22s local t %s world t %s scale %.3f' % (
            kind, b['name'], parent['name'] if parent else '-', np.round(b['translation'], 3), np.round(wt, 3), ws)
        if 'data' in b:
            g = nif.blocks[b['data']]
            v = g['vertices'] @ wr.T * ws + wt
            line += ' | verts %d tris %d min %s max %s | %s' % (len(v), len(g['triangles']), np.round(v.min(0), 2), np.round(v.max(0), 2),
                                                               [t.split('\\')[-1] for t in nif.textures(b)[:2]])
        print(line)
        if not np.allclose(b['rotation'], np.eye(3), atol=1e-4):
            print('             rotation', np.round(b['rotation'], 3).tolist())


if __name__ == '__main__':
    for f in sys.argv[1:]:
        print(f)
        main(f)
