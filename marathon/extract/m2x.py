"""Marathon: the packages of the game, through the modules of d2x (destiny/extract/d2x, not changed).

A program that imports this module runs with the Python of the environment of d2x:

    ./port marathon find "M77"
    PYTHONPATH=destiny/extract data/destiny/extract/venv/bin/python marathon/extract/m2x_extract.py --find "M77"

The game folder is the setting `marathon_game` (MARATHON_GAME, or data/config.toml). The
packages are in its folder `packages`; MARATHON_PACKAGES names another packages folder. The
package reader is tiger-pkg with its version `goliath`. Marathon has Oodle 9:
data/marathon/extract/runtime has the shim liboodle-data-shared.so (oodle9/oodle9.c) and a link
to oo2core_9_win64.dll of the game. setup.sh makes that folder and the table of the 64-bit tag
hashes (data/marathon/extract/notes/tag64.tsv).
"""
import importlib.util
import os
import sys

sys.dont_write_bytecode = True
_r = os.path.dirname(os.path.abspath(__file__))
while not os.path.isfile(os.path.join(_r, 'portkit', '__init__.py')) and _r != os.path.dirname(_r):
    _r = os.path.dirname(_r)
sys.path.insert(0, _r)
from portkit import paths  # noqa: E402

_absent = [name for name in ('numpy', 'PIL', 'texture2ddecoder', 'pyglm', 'pygltflib') if importlib.util.find_spec(name) is None]
if _absent:
    raise SystemExit('This Python (%s) does not have the module %s. Run the program with the Python of the environment of d2x: '
                     '%s (`./port destiny setup` makes it), or with `./port marathon ...`.' % (
                         sys.executable, ', '.join(_absent), paths.data('destiny', 'extract', 'venv', 'bin', 'python')))
if paths.repo('destiny', 'extract') not in sys.path:
    sys.path.insert(1, paths.repo('destiny', 'extract'))      # the modules of d2x
from d2x import pkg  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
RUNTIME = paths.data('marathon', 'extract', 'runtime')      # the Oodle 9 shim, the link to the library of the game, tag64
NOTES = paths.data('marathon', 'extract', 'notes')          # tag64.tsv, and the results of the programs of notes/
OUT = paths.data('marathon', 'extract', 'out')              # the default output folder of m2x_extract.py
SETUP = './port marathon setup (or: bash marathon/extract/setup.sh)'


def packages_folder():
    """The folder `packages` of the game: MARATHON_PACKAGES, or `packages` in the game folder."""
    return os.environ.get('MARATHON_PACKAGES') or os.path.join(paths.require('marathon_game'), 'packages')


def open_packages():
    packages = packages_folder()
    if not os.path.isdir(packages):
        raise SystemExit('The packages folder %s is not there. Give the game folder of Marathon in the setting `marathon_game` '
                         '(MARATHON_GAME), or the packages folder in MARATHON_PACKAGES.' % packages)
    for name in ('liboodle-data-shared.so', 'oo2core_9_win64.dll'):
        if not os.path.isfile(os.path.join(RUNTIME, name)):       # a link to a file that is not there is also missing
            raise SystemExit('%s is missing. Run %s.' % (os.path.join(RUNTIME, name), SETUP))
    return pkg.PackageManager(packages=packages, version='goliath', runtime=RUNTIME)


# ---- strings -------------------------------------------------------------------------------
# The layouts are those of Destiny 2 after Beyond Light with other class numbers.
STRING_CONTAINER = 0x8080B9B8      # hashes at 0x08; the tag of the English text at 0x18
STRING_DATA = 0x8080B9BA           # parts at 0x08 (0x20 bytes each), the text bytes at 0x28, the strings at 0x38


def _array(data, offset):
    """(count, start of the first item) of an array: the count at `offset`, a relative pointer at offset + 8.
    The pointer goes to a header of 16 bytes (count, class number); the items are after it."""
    import struct
    count, relative = struct.unpack_from('<qq', data, offset)
    return (count, offset + 8 + relative + 16) if count else (0, 0)


def read_string_data(data):
    """Each string of one string data tag, in index order. A string is one or more parts."""
    import struct
    part_count, parts = _array(data, 0x08)
    count, combos = _array(data, 0x38)
    out = []
    for i in range(count):
        o = combos + i * 0x10
        first = o + struct.unpack_from('<q', data, o)[0]
        n = struct.unpack_from('<q', data, o + 8)[0]
        text = []
        for j in range(n):
            part = first + j * 0x20
            pointer = part + 8 + struct.unpack_from('<q', data, part + 8)[0]
            length, = struct.unpack_from('<H', data, part + 0x14)
            text.append(data[pointer:pointer + length].decode('utf-8', 'replace'))
        out.append(''.join(text))
    return out


def read_container(pm, tag):
    """{string hash: English text} of one string container."""
    import struct
    import numpy as np
    data = pm.read(tag)
    count, start = _array(data, 0x08)
    hashes = np.frombuffer(data, dtype='<u4', count=count, offset=start)
    english, = struct.unpack_from('<I', data, 0x18)
    if not pm.exists(english):
        return {}
    strings = read_string_data(pm.read(english, cache=False))
    return {int(h): strings[i] for i, h in enumerate(hashes) if i < len(strings)}


def tag64_table(path=None):
    """{64-bit tag hash: (tag, class)} from data/marathon/extract/notes/tag64.tsv (the output of the program tag64)."""
    out = {}
    path = path or os.path.join(NOTES, 'tag64.tsv')
    if not os.path.isfile(path):
        raise SystemExit('%s is missing: the table of the 64-bit tag hashes. Run %s.' % (path, SETUP))
    with open(path) as f:
        for line in f:
            h, t, c = line.split('\t')[:3]
            if h != 'name':
                out[int(h, 16)] = (int(t, 16), int(c, 16))
    return out


# ---- the item database ---------------------------------------------------------------------
# Each table is found by its class, so another build with the same classes works.
DISPLAY_MAP = 0x80806EF0           # rows of 0x20 bytes: item hash at 0x00, display definition tag at 0x10
DISPLAY_DEFINITION = 0x80806EF6    # string container index at 0xBC, name hash at 0xC0
ITEM_MAP = 0x80809685              # rows of 0x20 bytes: item hash at 0x00, item definition tag at 0x10
ITEM_DEFINITION = 0x8080968B
CONTAINER_INDEX = 0x808071C8       # rows of 0x18 bytes: the 64-bit hash of a string container at 0x10
ART_TABLE = 0x80806CAC             # rows of 0x48 bytes: item hash at 0x00, entity assignment hash at 0x08
ENTITY_ASSIGNMENTS = 0x8080B61C    # rows of 0x18 bytes: assignment hash at 0x00, the 64-bit hash of an entity at 0x10


class Investment:
    """Item name -> item hash -> entity."""

    def __init__(self, pm, t64=None):
        import struct
        import numpy as np
        self.pm, self.t64 = pm, t64 or tag64_table()
        self._struct, self._np = struct, np
        self.display = self._rows(DISPLAY_MAP, 0x20, 0x10)
        self.items = self._rows(ITEM_MAP, 0x20, 0x10)
        data = pm.read(self._largest(CONTAINER_INDEX))
        count, start = _array(data, 0x08)
        self.containers = [self._resolve(struct.unpack_from('<Q', data, start + i * 0x18 + 0x10)[0]) for i in range(count)]
        self.art = self._rows(ART_TABLE, 0x48, 0x08)
        data = pm.read(self._largest(ENTITY_ASSIGNMENTS))
        count, start = _array(data, 0x08)
        self.assignments = {struct.unpack_from('<I', data, start + i * 0x18)[0]: struct.unpack_from('<Q', data, start + i * 0x18 + 0x10)[0]
                            for i in range(count)}
        self._strings = {}
        self._names = None

    def _largest(self, cls):
        e = self.pm.entries
        rows = e[(e['reference'] == cls) & (e['type'] == 8)]
        if len(rows) == 0:
            raise LookupError('no tag of the class %08X: the layouts of this file are for another build' % cls)
        return int(rows['tag'][self._np.argmax(rows['size'])])

    def _rows(self, cls, size, value_at):
        data = self.pm.read(self._largest(cls))
        count, start = _array(data, 0x08)
        u = self._struct.unpack_from
        return {u('<I', data, start + i * size)[0]: u('<I', data, start + i * size + value_at)[0] for i in range(count)}

    def _resolve(self, hash64):
        found = self.t64.get(hash64)
        return found[0] if found else 0

    def name(self, item_hash):
        tag = self.display.get(item_hash)
        if not tag or not self.pm.exists(tag):
            return ''
        data = self.pm.read(tag, cache=False)
        index, key = self._struct.unpack_from('<II', data, 0xBC)
        if index >= len(self.containers):
            return ''
        if index not in self._strings:
            tag = self.containers[index]
            self._strings[index] = read_container(self.pm, tag) if tag and self.pm.exists(tag) else {}
        return self._strings[index].get(key, '')

    def names(self):
        if self._names is None:
            self._names = {h: n for h in self.display for n in [self.name(h)] if n}
        return self._names

    def find(self, text):
        """Item hashes whose name has `text`; an item with exactly this name is first."""
        text = text.lower()
        found = sorted((n.lower() != text, n, h) for h, n in self.names().items() if text in n.lower())
        return [h for _, _, h in found]

    def entity(self, item_hash):
        """The entity of an item (its row of the art table), or 0."""
        assignment = self.art.get(item_hash)
        return self._resolve(self.assignments.get(assignment, 0)) if assignment else 0


# ---- entities ------------------------------------------------------------------------------
ENTITY = 0x8080BAAD                # components at 0x08: rows of 12 bytes with a component tag
COMPONENT = 0x8080BADB             # pointers at 0x10 and 0x18; the class of each block is 4 bytes before it
SKELETON = (0x80809FB6, 0x80809FB7)
RIG = (0x8080AD85, 0x8080AD7E)
MODEL = (0x80808673, 0x80808678)
MODEL_TAG = 0x8080881C
ANIMATION_SET = 0x80803BE9         # a list of clips, each one a 64-bit tag hash
CLIP = 0x8080AE01


class Component:
    def __init__(self, tag, data):
        import struct
        self.tag, self.data = tag, data
        p10 = 0x10 + struct.unpack_from('<q', data, 0x10)[0]
        p18 = 0x18 + struct.unpack_from('<q', data, 0x18)[0]
        ok = lambda p: 4 <= p <= len(data)
        self.kind = (struct.unpack_from('<I', data, p10 - 4)[0] if ok(p10) else 0, struct.unpack_from('<I', data, p18 - 4)[0] if ok(p18) else 0)
        self.definition = p18


def tags_in(pm, data, cls=None, t64=None):
    """The tags that a block names, in order, one time each: 32-bit tags, and with `t64` also 64-bit hashes."""
    import struct
    import numpy as np
    out = []
    words = np.frombuffer(data[:len(data) & ~3], dtype='<u4')
    for o in np.nonzero((words > 0x80810000) & (words <= 0x81FFFFFF))[0].tolist():
        v = int(words[o])
        if v not in out and pm.exists(v) and (cls is None or pm.reference(v) == cls) and pm.entry(v)['type'] == 8:
            out.append(v)
    if t64:
        for o in range(0, len(data) - 8, 4):
            found = t64.get(struct.unpack_from('<Q', data, o)[0])
            if found and found[0] not in out and (cls is None or found[1] == cls):
                out.append(found[0])
    return out


def read_entity(pm, tag):
    """The components of an entity, in order."""
    import struct
    data = pm.read(tag)
    count, start = _array(data, 0x08)
    out = []
    for i in range(count):
        c = struct.unpack_from('<I', data, start + i * 12)[0]
        if pm.exists(c) and pm.reference(c) == COMPONENT:
            out.append(Component(c, pm.read(c)))
    return out


def child_entities(pm, tag, t64):
    """The entities that the components of an entity name with a 64-bit hash."""
    out = []
    for c in read_entity(pm, tag):
        for t in tags_in(pm, c.data, None, t64):
            if pm.reference(t) == ENTITY and t not in out and t != tag:
                out.append(t)
    return out


# ---- models --------------------------------------------------------------------------------
# The layout is that of Destiny 2 after Beyond Light with other offsets:
#   model: meshes at 0x10 (0x80 bytes each), scale at 0xA0, translation at 0xB0,
#          texture coordinate scale (2 floats) and translation (2 floats) at 0xC0
#   mesh:  vertex buffer 0, vertex buffer 1, -, -, index buffer, color buffer, skin buffer (tags);
#          parts at 0x20 (0x28 bytes each); 26 part offsets of the 25 render stages at 0x30
#   part:  material at 0x00, primitive type at 0x06 (5: triangle strip), index offset at 0x08,
#          index count at 0x0C, detail level at 0x1C (16 bits)
STAGE_OPAQUE = 0
DETAIL_HIGH = (1,)


def _buffer(pm, tag):
    import struct
    size, stride, kind = struct.unpack_from('<IHH', pm.read(tag), 0)
    return pm.read(pm.reference(tag), cache=False)[:size], stride


def read_model(pm, model_tag, stages=(STAGE_OPAQUE,), detail=DETAIL_HIGH):
    """The parts of a model as d2x.model.Part objects. `detail` None: each detail level."""
    import struct
    import numpy as np
    from d2x.model import Part, _strip_runs
    data = pm.read(model_tag)
    scale = np.array(struct.unpack_from('<3f', data, 0xA0), np.float32)
    translation = np.array(struct.unpack_from('<3f', data, 0xB0), np.float32)
    uv_scale = np.array(struct.unpack_from('<2f', data, 0xC0), np.float32)
    uv_translation = np.array(struct.unpack_from('<2f', data, 0xC8), np.float32)
    count, start = _array(data, 0x10)
    parts = []
    for m in range(count):
        mesh = start + m * 0x80
        v0, v1, _, _, index_tag = struct.unpack_from('<5I', data, mesh)
        if not pm.exists(v0) or not pm.exists(index_tag):
            continue
        b0, s0 = _buffer(pm, v0)
        b1, s1 = _buffer(pm, v1) if pm.exists(v1) else (b'', 0)
        header = pm.read(index_tag)
        raw = pm.read(pm.reference(index_tag), cache=False)[:struct.unpack_from('<Q', header, 8)[0]]
        wide = len(raw) // 4 > 0 and header[0] != 1          # 1: 16-bit indices
        indices = np.frombuffer(raw, dtype='<u4' if wide else '<u2')
        restart = 0xFFFFFFFF if wide else 0xFFFF
        if s0 < 8:
            raise NotImplementedError('model %08X: a vertex buffer with %d bytes for each vertex' % (model_tag, s0))
        a = np.frombuffer(b0, dtype='<i2', count=(len(b0) // s0) * (s0 // 2)).reshape(-1, s0 // 2)
        uv = np.frombuffer(b1, dtype='<i2', count=(len(b1) // s1) * (s1 // 2)).reshape(-1, s1 // 2) if s1 >= 4 else None
        offsets = struct.unpack_from('<26H', data, mesh + 0x30)
        part_count, part_start = _array(data, mesh + 0x20)
        for stage in stages:
            for index in range(offsets[stage], offsets[stage + 1]):
                if index >= part_count:
                    continue
                po = part_start + index * 0x28
                material, variant, primitive, first, n = struct.unpack_from('<IhHII', data, po)
                level, = struct.unpack_from('<H', data, po + 0x1C)
                if detail is not None and level not in detail:
                    continue
                chunk = indices[first:first + n]
                triangles = _strip_runs(chunk, restart) if primitive == 5 else chunk[:len(chunk) // 3 * 3].astype(np.uint32).reshape(-1, 3)
                if len(triangles) == 0:
                    continue
                used, remap = np.unique(triangles, return_inverse=True)
                rows = a[used]
                positions = rows[:, :3].astype(np.float32) / 32767.0 * scale + translation
                joints = np.zeros((len(used), 4), np.uint16)
                weights = np.zeros((len(used), 4), np.float32)
                weights[:, 0] = 1.0
                joints[:, 0] = np.clip(rows[:, 3], 0, None)           # rigid skin: the bone index is the fourth position value
                normals = rows[:, 4:7].astype(np.float32) / 32767.0 if s0 >= 16 else None
                tangents = rows[:, 8:12].astype(np.float32) / 32767.0 if s0 >= 24 else None
                uvs = uv[used, :2].astype(np.float32) / 32767.0 * uv_scale + uv_translation if uv is not None else None
                parts.append(Part(m, index, stage, level, material, positions.astype(np.float32), normals, tangents, uvs, None,
                                  joints, weights, remap.reshape(-1, 3).astype(np.uint32), flags=struct.unpack_from('<I', data, po + 0x18)[0],
                                  extra={'strides': (s0, s1), 'primitive': primitive, 'variant': variant}))
    return parts


# ---- materials and textures ----------------------------------------------------------------
MATERIAL = 0x808031D8              # the textures of the pixel shader: rows of 0x18 bytes of the class 808086C6
TEXTURE_ROWS = 0x808086C6          # slot at 0x00, the 64-bit hash of the texture at 0x10


def material_textures(pm, material_tag, t64):
    """[(slot, texture tag)] of a material."""
    import struct
    import numpy as np
    data = pm.read(material_tag)
    words = np.frombuffer(data[:len(data) & ~3], dtype='<u4')
    out = []
    for o in np.nonzero(words == TEXTURE_ROWS)[0].tolist():
        header = o * 4 - 8
        count = struct.unpack_from('<Q', data, header)[0]
        for i in range(count):
            row = header + 16 + i * 0x18
            slot, _, hash64 = struct.unpack_from('<QQQ', data, row)
            found = t64.get(hash64)
            if found and pm.exists(found[0]):
                out.append((int(slot), found[0]))
    return out


def read_texture(pm, tag):
    """(pixels (h, w, 4) uint8 RGBA, info) of the largest level of a texture.
    The header: data size at 0x00, DXGI format at 0x04, width, height, depth and array size
    (16 bits each) at 0x22, the tag of the data of the large levels at 0x3C."""
    import struct
    import numpy as np
    import texture2ddecoder
    from d2x import texture as tex
    header = pm.read(tag)
    dxgi, = struct.unpack_from('<I', header, 4)
    width, height, depth, layers = struct.unpack_from('<4H', header, 0x22)
    large, = struct.unpack_from('<I', header, 0x3C)
    data = pm.read(large if pm.exists(large) else pm.reference(tag), cache=False)
    srgb = (tex._BLOCK.get(dxgi) or tex._RAW.get(dxgi) or ('', False))[1]
    info = tex.TextureInfo(tag, width, height, depth, layers, dxgi, srgb)
    if dxgi in tex._BLOCK:
        kind = tex._BLOCK[dxgi][0]
        raw = getattr(texture2ddecoder, 'decode_' + kind)(data, width, height)
        pixels = np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 4)[:, :, [2, 1, 0, 3]]
        if kind == 'bc4':
            pixels = pixels.copy()
            pixels[:, :, 1] = pixels[:, :, 0]
            pixels[:, :, 2] = pixels[:, :, 0]
        return np.ascontiguousarray(pixels), info
    if dxgi in tex._RAW:
        order = tex._RAW[dxgi][0]
        if order in ('RGBA', 'BGRA'):
            pixels = np.frombuffer(data, dtype=np.uint8, count=width * height * 4).reshape(height, width, 4)
            return np.ascontiguousarray(pixels[:, :, [2, 1, 0, 3]] if order == 'BGRA' else pixels), info
        gray = np.frombuffer(data, dtype=np.uint8, count=width * height).reshape(height, width)
        return np.dstack([gray, gray, gray, np.full_like(gray, 255)]), info
    raise NotImplementedError('DXGI format %d of the texture %08X' % (dxgi, tag))


# ---- skeletons, rigs and clips -------------------------------------------------------------
# The decoder is tiger-animation-parser (the clone of d2x, data/destiny/extract/vendor) with its
# version `marathon`. Its offsets of the skeleton and of the rig are those of an earlier build:
# in this build the two blocks start 16 bytes earlier (skeleton: 0xB0 in the second block; rig:
# 0x98). The parser is not changed: this function gives it a pointer that is 16 bytes lower, in
# this process only. A process that calls it must not read a rig of Destiny 2 (the row size of a
# relation is then wrong).
def patch_parser():
    from d2x import anim  # noqa: F401  (puts the parser on the path)
    import tag_readers.read_skeleton as rs
    import tag_readers.read_rig as rr
    from tag.game_version import Game_Version

    class Shifted:
        def __init__(self, pointer, by):
            self.pointer, self.by = pointer, by

        def get_address(self):
            return self.pointer.get_address() + self.by

    if getattr(rs, '_m2x_patch', False):
        return
    skeleton_main, rig_main = rs.read_skeleton_main_struct, rr.read_runtime_rig_main_struct
    rs.read_skeleton_main_struct = lambda f, p, v: skeleton_main(f, Shifted(p, -0x10) if v == Game_Version.MARATHON else p, v)
    rr.read_runtime_rig_main_struct = lambda f, p, v: rig_main(f, Shifted(p, -0x10) if v == Game_Version.MARATHON else p, v)
    # A control relation of the rig has the fields of Destiny 2 (52 bytes) and 20 more bytes.
    relation = rr.read_control_relation_d2

    def relation_72(f, endianness):
        row = relation(f, endianness)
        f.seek(20, 1)
        return row
    rr.read_control_relation_d2 = relation_72
    rs._m2x_patch = True


# ---- names ---------------------------------------------------------------------------------
# The game has only the FNV-1 hash of each name. These words were found with a word list
# against the hashes of the M77 (bones, rig controls, slots of the weapon, animation names).
WORDS = ('b_handle b_magazine b_bolt b_bullet_1 b_bullet_2 b_casing b_mag_release b_safety b_trigger b_bolt_handle b_anim b_scope_1 b_scope_2 '
         'handle magazine bolt bullet_1 bullet_2 casing mag_release safety trigger bolt_handle '
         'barrel sight foregrip chip charm sticker attachment base base_overlay reload_1 reload_enter chamber_1 sprint_ready '
         'rifle pistol shotgun smg sniper_rifle railgun dmr lmg hmg ar magnum knife unarmed grenade sniper stand crouch empty partial full grip').split()


def _fnv1(text):
    value = 0x811C9DC5
    for byte in text.encode():
        value = ((value * 0x01000193) & 0xFFFFFFFF) ^ byte
    return value


NAMES = {_fnv1(w): w for w in WORDS}


def name_of(value, prefix=''):
    """The word of a hash, or PREFIX + the hash in hexadecimal."""
    from d2x import names
    if value in NAMES:
        return NAMES[value]
    known = names.KNOWN.get(value)
    return known if known else '%s%08X' % (prefix, value)


# ---- the slots of a weapon and its animation sets ------------------------------------------
WEAPON_PARTS = (0x80804603, 0x80804A14)   # the component with the slots: rows of 0x20 bytes of the class 8080460A
SLOT_ROWS = 0x8080460A                    # slot name hash at 0x00, the 64-bit hash of the default entity at 0x18
SET_ROWS = 0x8080ADFF                     # rows of 0x30 bytes of an animation set: name hash at 0x10, clip (64-bit) at 0x20
ATTACH = (0x808032C2, 0x808032C4)         # the component of a piece that names its slot


def _rows(data, cls, size):
    """The offset of each row of each array of a class in a block."""
    import struct
    import numpy as np
    words = np.frombuffer(data[:len(data) & ~3], dtype='<u4')
    out = []
    for o in np.nonzero(words == cls)[0].tolist():
        header = o * 4 - 8
        count = struct.unpack_from('<Q', data, header)[0]
        if 0 < count < 4096 and header + 16 + count * size <= len(data):
            out += [header + 16 + i * size for i in range(count)]
    return out


def weapon_slots(pm, components, t64):
    """[(slot name hash, default entity tag or 0)] of a weapon entity."""
    import struct
    out = []
    for c in components:
        if c.kind == WEAPON_PARTS:
            for row in _rows(c.data, SLOT_ROWS, 0x20):
                found = t64.get(struct.unpack_from('<Q', c.data, row + 0x18)[0])
                out.append((struct.unpack_from('<I', c.data, row)[0], found[0] if found else 0))
    return out


def rig_controls(component):
    """{control name hash: bone index} of a rig component (0x118 in its second block)."""
    import struct
    data = component.data
    count, start = _array(data, component.definition + 0x118)
    return {struct.unpack_from('<I', data, start + i * 8)[0]: struct.unpack_from('<I', data, start + i * 8 + 4)[0] for i in range(count)}


def animation_set(pm, tag, t64):
    """[(animation name hash, clip tag)] of an animation set, in order."""
    import struct
    data = pm.read(tag)
    out = []
    for row in _rows(data, SET_ROWS, 0x30):
        found = t64.get(struct.unpack_from('<Q', data, row + 0x20)[0])
        if found and found[1] == CLIP:
            out.append((struct.unpack_from('<I', data, row + 0x10)[0], found[0]))
    return out


# ---- the places of the pieces --------------------------------------------------------------
# An entity has named points (markers). A piece of a weapon names one point of the weapon, and
# its own point `attachment` goes there. A point is on a bone of the skeleton of its entity.
MARKERS = (0x80809F75, 0x80809F76)
MARKER_ROWS = 0x80809F82           # rows of 0x30 bytes: rotation (x, y, z, w), translation, scale, 4 bytes, bone index, name hash, number
ATTACH_ROW = 0x808032C9            # in the component ATTACH of a piece: the next value is the name of the point of the weapon
ATTACHMENT = _fnv1('attachment')


def markers(components):
    """{name hash: (bone index, rotation (x, y, z, w), translation, scale)} of an entity, in the axes of the game."""
    import struct
    out = {}
    for c in components:
        if c.kind == MARKERS:
            for row in _rows(c.data, MARKER_ROWS, 0x30):
                q = struct.unpack_from('<4f', c.data, row)
                t = struct.unpack_from('<4f', c.data, row + 16)
                _, bone, name, _ = struct.unpack_from('<4I', c.data, row + 32)
                out.setdefault(name, (bone, q, t[:3], t[3]))
    return out


def attach_point(components):
    """The name hash of the point of the weapon where a piece goes, or None."""
    import struct
    import numpy as np
    for c in components:
        if c.kind == ATTACH:
            words = np.frombuffer(c.data[:len(c.data) & ~3], dtype='<u4')
            for o in np.nonzero(words == ATTACH_ROW)[0].tolist():
                if o + 2 < len(words) and int(words[o + 2]) == ATTACHMENT:
                    return int(words[o + 1])
    return None


def marker_matrix(marker):
    """The 4 x 4 matrix of a point in the space of its bone (the axes of the game)."""
    import numpy as np
    _, (x, y, z, w), t, scale = marker
    m = np.eye(4)
    m[:3, :3] = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                          [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                          [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]]) * scale
    m[:3, 3] = t
    return m


# ---- the animation graph -------------------------------------------------------------------
# The layout is that of the graph of Destiny 2 (d2x/graph.py) with other classes, a node of
# 0x24 bytes (a tag mask of 24 bytes, value hash, child, next, link) and one tag tree for each
# dimension:
#   graph     0x08 (state name hash, state index); 0x18 (kind, pointer) for each state
#             kind 1: a list of (set entry, threshold). kind 2: 0x00 the lists, 0x10 the
#             dimensions, 0x20 the nodes, 0x30 the groups (dimension, first node)
#   tag trees 0x08 one row of 0x20 bytes for each tree, with the tags (hash, parent);
#             0x18 the tree of each dimension number (16 bits each, FFFF: none)
#   set       0x08 the clips (rows of 0x10 bytes, a 64-bit hash at 0x08); 0x58 the entries (rows
#             of 0x30 bytes: name hash at 0x10, clip hash at 0x20, clip index at 0x28)
ANIMATION = (0x80803951, 0x80803936)      # the component with the set, the graph and the tag trees
GRAPH = 0x80803950
TAG_TREES = 0x8080ACBF
WEAPON_DIMENSION = 3
NODE = 0x24
EMPTY = 0x811C9DC5                        # the hash of an empty word: the top of each tree


def tag_trees(data):
    """(the tree index of each dimension number, the trees: a list of (tag hash, parent index or -1))."""
    import struct
    count, start = _array(data, 0x08)
    trees = []
    for i in range(count):
        n, at = _array(data, start + i * 0x20)
        rows = [struct.unpack_from('<IH', data, at + k * 8) for k in range(n)]
        trees.append([(h, -1 if p == 0xFFFF else p) for h, p in rows])
    index = [v if v != 0xFFFF else -1 for v in struct.unpack_from('<32H', data, 0x18)]
    return index, trees


def tag_chain(tree, tag):
    """A tag and each tag above it, the top of the tree not included."""
    index = {h: i for i, (h, _) in enumerate(tree)}
    out, i = [], index.get(tag, -1)
    while i > 0 and tree[i][0] not in out:
        out.append(tree[i][0])
        i = tree[i][1]
    return out


def weapon_tag_pair(components, tree):
    """(class tag, weapon tag) of a weapon entity: two tags of the weapon tree, one after the other, in its slots component."""
    import numpy as np
    known = {h for h, _ in tree if h != EMPTY}
    for c in components:
        if c.kind == WEAPON_PARTS:
            words = np.frombuffer(c.data[:len(c.data) & ~3], dtype='<u4').tolist()
            for a, b in zip(words, words[1:]):
                if a in known and b in known:
                    return a, b
    return None


def set_tables(pm, tag, t64):
    """(the clip tags, the entries (name hash, clip tag or 0)) of an animation set. A number of the graph is an entry."""
    import struct
    data = pm.read(tag)
    count, start = _array(data, 0x08)
    clips = [t64.get(struct.unpack_from('<Q', data, start + i * 0x10 + 8)[0], (0, 0))[0] for i in range(count)]
    count, start = _array(data, 0x58)
    entries = []
    for i in range(count):
        row = start + i * 0x30
        found = t64.get(struct.unpack_from('<Q', data, row + 0x20)[0])
        entries.append((struct.unpack_from('<I', data, row + 0x10)[0], found[0] if found and found[1] == CLIP else 0))
    return clips, entries


def read_graph(data, tags):
    """[(state index, [name hash], [(conditions, weapon tag, [(set entry, threshold)])])] for the weapon
    tags `tags` (the most specific tag first). A condition is (dimension number, value hash)."""
    import struct
    u = struct.unpack_from

    def lists(offset):
        count, start = _array(data, offset)
        return [(u('<I', data, start + i * 8)[0], round(u('<f', data, start + i * 8 + 4)[0], 3)) for i in range(count)]
    count, start = _array(data, 0x08)
    names = {}
    for i in range(count):
        names.setdefault(u('<I', data, start + i * 8 + 4)[0], []).append(u('<I', data, start + i * 8)[0])
    rank = {tag: position for position, tag in enumerate(tags)}
    count, states_at = _array(data, 0x18)
    out = []
    for index in range(count):
        kind, relative = u('<Qq', data, states_at + index * 16)
        base = states_at + index * 16 + 8 + relative
        choices = []
        out.append((index, names.get(index, []), choices))
        if kind == 1:
            choices.append(((), 0, lists(base)))
            continue
        n, at = _array(data, base)
        entries = [lists(at + i * 16) for i in range(n)]
        node_count, nodes_at = _array(data, base + 0x20)
        n, at = _array(data, base + 0x30)
        groups = [u('<HH', data, at + i * 4) for i in range(n)]

        def node(i):
            return u('<Ihhh', data, nodes_at + i * NODE + 24)           # value, child, next, link

        def follow(link, conditions, tag):
            if link > 0:
                walk(link - 1, conditions, tag)
            elif link < 0 and -link - 1 < len(entries):
                choices.append((conditions, tag, entries[-link - 1]))

        def weapon_node(first):
            """The node of the most specific tag of the weapon: (tag, link)."""
            best, stack = None, [first]
            while stack:
                i = stack.pop()
                if not 0 <= i < node_count:
                    continue
                tag, child, sibling, link = node(i)
                if sibling >= 0:
                    stack.append(sibling)
                if tag in rank:
                    if link != 0 and (best is None or rank[tag] < rank[best[0]]):
                        best = (tag, link)
                    if child >= 0:
                        stack.append(child)
            return best

        def walk(group, conditions, tag):
            if not 0 <= group < len(groups):
                return
            dimension, first = groups[group]
            if dimension == WEAPON_DIMENSION:
                found = weapon_node(first)
                if found:
                    follow(found[1], conditions, found[0])
                return
            stack, seen = [first], set()
            while stack:
                i = stack.pop(0)
                if not 0 <= i < node_count or i in seen:
                    continue
                seen.add(i)
                value, child, sibling, link = node(i)
                follow(link, conditions + ((dimension, value),), tag)
                stack = [x for x in (child, sibling) if x >= 0] + stack
        walk(0, (), 0)
    return out


# ---- a material in the form of Destiny 2 ---------------------------------------------------
# The tools of destiny/port read a texture set of Destiny 2: albedo (color), normal, and gstack (red:
# occlusion, green: smoothness, blue: emission, alpha: 0 to 32 is the metal value). The rules
# are from the pixel shaders of the materials of the M77 (DXIL; notes/dxil.py prints one):
#   detail    6 textures. Color = texture 0 x the color of a region x a detail value. Texture 3
#             has the regions (red, green, blue) and the smoothness (alpha). The file has the
#             color of the region 0 only (0.216, which gives the color of texture 0 with no
#             change); the game calculates the colors of the six other regions when it runs.
#             Occlusion = the alpha of texture 0. Metal = texture 2 (black in each file here).
#   palette   1 or 2 textures. Color = texture 0 (an atlas of flat colors). Smoothness = one
#             value of the constants. No normal map, no metal.
#   constant  no texture: one color of the constants (a light of the sight). Emission is not done.
VECTORS = 0x80800090


def material_constants(data):
    """The values of the constant buffer of the pixel shader: the last table of vectors of the tag (n x 4)."""
    import struct
    import numpy as np
    found = None
    for o in range(0, len(data) - 16, 8):
        count, cls, pad = struct.unpack_from('<QII', data, o)
        if cls == VECTORS and pad == 0 and 0 < count < 4096 and o + 16 + count * 16 <= len(data):
            found = np.frombuffer(data, '<f4', count * 4, o + 16).reshape(count, 4)
    return found if found is not None else np.zeros((0, 4), np.float32)


def material_plates(pm, material, t64, read=None):
    """({'albedo', 'normal', 'gstack'}: pixels (h, w, 4) uint8, a record of the rule) for a material."""
    import numpy as np
    from PIL import Image
    read = read or (lambda tag: read_texture(pm, tag))
    rows = {}
    for slot, tag in material_textures(pm, material, t64):
        try:
            rows[slot] = (tag,) + tuple(read(tag))
        except Exception:
            pass
    cb = material_constants(pm.read(material))

    def sized(pixels, size):
        return pixels if (pixels.shape[1], pixels.shape[0]) == size else np.asarray(Image.fromarray(pixels).resize(size, Image.BILINEAR))
    record = {'textures': {str(s): '%08X' % r[0] for s, r in sorted(rows.items())}, 'metal': 0.0}
    if len(rows) >= 4 and 0 in rows and 3 in rows and rows[0][2].srgb and not rows[3][2].srgb:
        base = rows[0][1]
        size = (base.shape[1], base.shape[0])
        mask = sized(rows[3][1], size)
        albedo = np.dstack([base[:, :, :3], np.full(base.shape[:2], 255, np.uint8)])
        gstack = np.dstack([base[:, :, 3], mask[:, :, 3], np.zeros(base.shape[:2], np.uint8), np.zeros(base.shape[:2], np.uint8)])
        normal = sized(rows[1][1], size) if 1 in rows else None
        regions = (mask[:, :, :3] > 127).reshape(-1, 3)
        record.update(rule='detail', smoothness='the alpha of the texture %08X' % rows[3][0], occlusion='the alpha of the texture %08X' % rows[0][0],
                      region_color=[round(float(x), 4) for x in cb[7][:3]] if len(cb) > 7 else None,
                      pixels_with_a_region=round(float(regions.any(axis=1).mean()), 3),
                      note='the colors of the regions of the texture %08X are not in the file: each region has the color of the region 0' % rows[3][0])
    elif 0 in rows:
        base = rows[0][1]
        # an atlas of flat colors: half the size is enough, with no mix of two colors
        if base.shape[0] > 1024:
            base = np.ascontiguousarray(base[1::2, 1::2])
        value = None
        for i in range(len(cb) - 2):
            if abs(cb[i + 1][0] - 0.86) < 1e-3 and abs(cb[i + 2][0] + 0.2) < 1e-3 and abs(cb[i + 2][1] - 1.8) < 1e-3:
                value = float(cb[i][0])
        if value is None and len(cb) and 0.0 < cb[-1][0] <= 1.0 and not cb[-1][1:].any():
            value = float(cb[-1][0])
        record.update(rule='palette', smoothness=round(value, 4) if value is not None else 0.3,
                      smoothness_from='the constants' if value is not None else 'a default: the constants do not give it')
        albedo = np.dstack([base[:, :, :3], np.full(base.shape[:2], 255, np.uint8)])
        gstack = np.zeros_like(albedo)
        gstack[:, :, 0] = 255
        gstack[:, :, 1] = int(round(record['smoothness'] * 255))
        normal = None
    else:
        color = np.clip(cb[0][:3], 0.0, 1.0) if len(cb) else np.array([0.5, 0.5, 0.5])
        srgb = np.where(color <= 0.0031308, color * 12.92, 1.055 * color ** (1 / 2.4) - 0.055)
        albedo = np.zeros((8, 8, 4), np.uint8)
        albedo[:, :, :3] = np.round(srgb * 255).astype(np.uint8)
        albedo[:, :, 3] = 255
        gstack = np.zeros_like(albedo)
        gstack[:, :, 0] = 255
        gstack[:, :, 1] = 171
        normal = None
        record.update(rule='constant', color=[round(float(x), 4) for x in (cb[0][:3] if len(cb) else color)], smoothness=0.67,
                      note='a color of the constants; its emission is not done')
    if normal is None:
        normal = np.zeros_like(albedo)
        normal[:, :, :2] = 128
        normal[:, :, 2:] = 255
    return {'albedo': albedo, 'normal': np.ascontiguousarray(normal), 'gstack': gstack}, record
