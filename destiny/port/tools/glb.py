"""Read a glTF binary file (.glb): the JSON part and the accessors as numpy arrays."""
import json
import struct
import numpy as np

CTYPE = {5120: 'i1', 5121: 'u1', 5122: '<i2', 5123: '<u2', 5125: '<u4', 5126: '<f4'}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


class Glb:
    def __init__(self, path):
        with open(path, 'rb') as f:
            data = f.read()
        magic, _, total = struct.unpack_from('<4sII', data, 0)
        if magic != b'glTF':
            raise SystemExit('%s is not a glTF binary file' % path)
        offset = 12
        chunks = []
        while offset < total:
            size, kind = struct.unpack_from('<II', data, offset)
            chunks.append(data[offset + 8:offset + 8 + size])
            offset += 8 + size
        self.path = path
        self.json = json.loads(chunks[0])
        self.bin = chunks[1] if len(chunks) > 1 else b''
        self.nodes = self.json['nodes']
        self.parent = {}
        for i, n in enumerate(self.nodes):
            for c in n.get('children', ()):
                self.parent[c] = i

    def accessor(self, index):
        a = self.json['accessors'][index]
        view = self.json['bufferViews'][a['bufferView']]
        dtype = np.dtype(CTYPE[a['componentType']])
        n = NCOMP[a['type']]
        start = view.get('byteOffset', 0) + a.get('byteOffset', 0)
        stride = view.get('byteStride')
        if stride and stride != dtype.itemsize * n:
            raw = np.frombuffer(self.bin, np.uint8, count=stride * a['count'], offset=start).reshape(a['count'], stride)
            arr = raw[:, :dtype.itemsize * n].copy().view(dtype).reshape(a['count'], n)
        else:
            arr = np.frombuffer(self.bin, dtype, count=a['count'] * n, offset=start).reshape(a['count'], n)
        if a.get('normalized'):
            return arr / float(np.iinfo(dtype).max)
        return arr.astype(np.float64) if dtype.kind == 'f' else arr

    def node_index(self, name):
        for i, n in enumerate(self.nodes):
            if n.get('name') == name:
                return i
        raise KeyError(name)
