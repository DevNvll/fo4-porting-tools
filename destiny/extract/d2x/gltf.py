"""Minimal binary glTF 2.0 (.glb) writer: skinned meshes, textures, animations."""
import json
import struct

import numpy as np

_COMPONENT = {
    np.dtype('float32'): 5126, np.dtype('uint32'): 5125, np.dtype('uint16'): 5123, np.dtype('uint8'): 5121,
}
ARRAY_BUFFER, ELEMENT_ARRAY_BUFFER = 34962, 34963


class GlbBuilder:
    def __init__(self, generator='d2x'):
        self.doc = {
            'asset': {'version': '2.0', 'generator': generator},
            'scene': 0, 'scenes': [{'nodes': []}], 'nodes': [],
            'meshes': [], 'accessors': [], 'bufferViews': [], 'buffers': [],
            'materials': [], 'textures': [], 'images': [], 'samplers': [],
            'skins': [], 'animations': [], 'cameras': [],
        }
        self.binary = bytearray()

    # -- raw data --------------------------------------------------------
    def view(self, data, target=None):
        while len(self.binary) % 4:
            self.binary.append(0)
        view = {'buffer': 0, 'byteOffset': len(self.binary), 'byteLength': len(data)}
        if target:
            view['target'] = target
        self.binary += data
        self.doc['bufferViews'].append(view)
        return len(self.doc['bufferViews']) - 1

    def accessor(self, array, kind, target=None, bounds=False, normalized=False):
        array = np.ascontiguousarray(array)
        accessor = {
            'bufferView': self.view(array.tobytes(), target),
            'componentType': _COMPONENT[array.dtype],
            'count': int(array.shape[0]),
            'type': kind,
        }
        if normalized:
            accessor['normalized'] = True
        if bounds:
            flat = array.reshape(array.shape[0], -1)
            accessor['min'] = [float(v) for v in flat.min(axis=0)]
            accessor['max'] = [float(v) for v in flat.max(axis=0)]
        self.doc['accessors'].append(accessor)
        return len(self.doc['accessors']) - 1

    # -- scene objects ---------------------------------------------------
    def node(self, name, parent=None, **fields):
        node = {'name': name, **fields}
        self.doc['nodes'].append(node)
        index = len(self.doc['nodes']) - 1
        if parent is None:
            self.doc['scenes'][0]['nodes'].append(index)
        else:
            self.doc['nodes'][parent].setdefault('children', []).append(index)
        return index

    def camera(self, name, yfov=0.9, znear=0.01, aspect=16 / 9):
        self.doc['cameras'].append({'name': name, 'type': 'perspective',
                                    'perspective': {'yfov': yfov, 'znear': znear, 'aspectRatio': aspect}})
        return len(self.doc['cameras']) - 1

    def texture(self, png_bytes, name):
        if not self.doc['samplers']:
            self.doc['samplers'].append({'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497})
        self.doc['images'].append({'name': name, 'mimeType': 'image/png', 'bufferView': self.view(png_bytes)})
        self.doc['textures'].append({'sampler': 0, 'source': len(self.doc['images']) - 1, 'name': name})
        return len(self.doc['textures']) - 1

    def material(self, name, base_color=None, normal=None, orm=None, emissive=None,
                 alpha_mode='OPAQUE', double_sided=False, color_factor=None):
        pbr = {'metallicFactor': 1.0 if orm is not None else 0.0, 'roughnessFactor': 1.0 if orm is not None else 0.6}
        if base_color is not None:
            pbr['baseColorTexture'] = {'index': base_color}
        if color_factor is not None:
            pbr['baseColorFactor'] = list(color_factor)
        if orm is not None:
            pbr['metallicRoughnessTexture'] = {'index': orm}
        material = {'name': name, 'pbrMetallicRoughness': pbr, 'doubleSided': double_sided}
        if normal is not None:
            material['normalTexture'] = {'index': normal}
        if orm is not None:
            material['occlusionTexture'] = {'index': orm}
        if emissive is not None:
            material['emissiveTexture'] = {'index': emissive}
            material['emissiveFactor'] = [1.0, 1.0, 1.0]
        if alpha_mode != 'OPAQUE':
            material['alphaMode'] = alpha_mode
            if alpha_mode == 'MASK':
                material['alphaCutoff'] = 0.5
        self.doc['materials'].append(material)
        return len(self.doc['materials']) - 1

    def primitive(self, positions, triangles, material=None, normals=None, tangents=None, uvs=None,
                  joints=None, weights=None, colors=None):
        attributes = {'POSITION': self.accessor(positions.astype(np.float32), 'VEC3', ARRAY_BUFFER, bounds=True)}
        if normals is not None:
            attributes['NORMAL'] = self.accessor(normals.astype(np.float32), 'VEC3', ARRAY_BUFFER)
        if tangents is not None:
            attributes['TANGENT'] = self.accessor(tangents.astype(np.float32), 'VEC4', ARRAY_BUFFER)
        if uvs is not None:
            attributes['TEXCOORD_0'] = self.accessor(uvs.astype(np.float32), 'VEC2', ARRAY_BUFFER)
        if colors is not None:
            attributes['COLOR_0'] = self.accessor(colors.astype(np.uint8), 'VEC4', ARRAY_BUFFER, normalized=True)
        if joints is not None:
            attributes['JOINTS_0'] = self.accessor(joints.astype(np.uint16), 'VEC4', ARRAY_BUFFER)
            attributes['WEIGHTS_0'] = self.accessor(weights.astype(np.float32), 'VEC4', ARRAY_BUFFER)
        primitive = {
            'attributes': attributes,
            'indices': self.accessor(triangles.astype(np.uint32).reshape(-1), 'SCALAR', ELEMENT_ARRAY_BUFFER),
            'mode': 4,
        }
        if material is not None:
            primitive['material'] = material
        return primitive

    def mesh(self, name, primitives):
        self.doc['meshes'].append({'name': name, 'primitives': primitives})
        return len(self.doc['meshes']) - 1

    def skin(self, name, joints, inverse_bind_matrices, skeleton_root=None):
        matrices = np.ascontiguousarray(inverse_bind_matrices, dtype=np.float32)
        # glTF stores matrices column-major.
        accessor = self.accessor(matrices.transpose(0, 2, 1).reshape(-1, 16), 'MAT4')
        skin = {'name': name, 'joints': list(joints), 'inverseBindMatrices': accessor}
        if skeleton_root is not None:
            skin['skeleton'] = skeleton_root
        self.doc['skins'].append(skin)
        return len(self.doc['skins']) - 1

    def animation(self, name, times, channels):
        """channels: list of (node index, path, values array).

        A channel with one row is a constant: it gets one key at the first time.
        """
        times = np.asarray(times, dtype=np.float32)
        time_accessor = self.accessor(times, 'SCALAR', bounds=True)
        single_accessor = None
        animation = {'name': name, 'samplers': [], 'channels': []}
        for node, path, values in channels:
            values = np.asarray(values, dtype=np.float32)
            kind = 'VEC4' if path == 'rotation' else 'VEC3'
            if len(values) == 1 and len(times) > 1:
                if single_accessor is None:
                    single_accessor = self.accessor(times[:1], 'SCALAR', bounds=True)
                input_accessor = single_accessor
            else:
                input_accessor = time_accessor
            animation['samplers'].append({
                'input': input_accessor,
                'output': self.accessor(values, kind),
                'interpolation': 'LINEAR',
            })
            animation['channels'].append({
                'sampler': len(animation['samplers']) - 1,
                'target': {'node': node, 'path': path},
            })
        self.doc['animations'].append(animation)
        return len(self.doc['animations']) - 1

    # -- output ----------------------------------------------------------
    def save(self, path):
        doc = {key: value for key, value in self.doc.items() if value not in ([], None)}
        while len(self.binary) % 4:
            self.binary.append(0)
        doc['buffers'] = [{'byteLength': len(self.binary)}]
        text = json.dumps(doc, separators=(',', ':')).encode()
        text += b' ' * (-len(text) % 4)
        total = 12 + 8 + len(text) + 8 + len(self.binary)
        with open(path, 'wb') as stream:
            stream.write(struct.pack('<4sII', b'glTF', 2, total))
            stream.write(struct.pack('<I4s', len(text), b'JSON'))
            stream.write(text)
            stream.write(struct.pack('<I4s', len(self.binary), b'BIN\0'))
            stream.write(self.binary)
        return total
