"""Package access through the tiger-pkg C wrapper (tigerpkg-ffi).

This module also has the folders of d2x. The source is in `destiny/extract` (ROOT). Each
generated or third-party file is below `data/destiny/extract` (DATA): `vendor/`, `runtime/`,
`venv/`, `target/`, `out/`. `setup.sh` makes them. The folders and the game folder come from
`portkit.paths`, so that this code has no path of one computer.
"""
import ctypes
import os
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]          # destiny/extract: the source of d2x

_repo = ROOT
while not (_repo / 'portkit' / '__init__.py').is_file() and _repo != _repo.parent:
    _repo = _repo.parent
if str(_repo) not in sys.path:
    sys.path.insert(0, str(_repo))
from portkit import paths                           # noqa: E402

DATA = Path(paths.data('destiny', 'extract'))       # data/destiny/extract: all that setup.sh and d2x make
VENDOR = DATA / 'vendor'                            # the clones of tiger-pkg and tiger-animation-parser
DEFAULT_LIBRARY = DATA / 'target/release/libtigerpkg_ffi.so'
DEFAULT_RUNTIME = DATA / 'runtime'                  # liblinoodle3.so and the link to the Oodle DLL of the game
DEFAULT_OUT = DATA / 'out'
DEFAULT_VERSION = os.environ.get('D2X_VERSION', 'd2_sk')
SETUP_HINT = 'Run `./port destiny setup` (or `destiny/extract/setup.sh`) first.'


def default_packages(required=True):
    """The `packages` folder of the game: D2X_PACKAGES, or the setting `destiny_game` plus `packages`.

    When there is no value: stops with advice (required), or returns None.
    """
    packages = os.environ.get('D2X_PACKAGES')
    if packages:
        return Path(packages).expanduser()
    game = paths.require('destiny_game') if required else paths.setting('destiny_game')
    return Path(game) / 'packages' if game else None


DEFAULT_PACKAGES = default_packages(required=False)   # None when the game folder has no setting

ENTRY_DTYPE = np.dtype([
    ('tag', '<u4'), ('reference', '<u4'), ('size', '<u4'),
    ('type', 'u1'), ('subtype', 'u1'), ('pkg_id', '<u2'),
])


class _Entry(ctypes.Structure):
    _fields_ = [
        ('tag', ctypes.c_uint32), ('reference', ctypes.c_uint32), ('size', ctypes.c_uint32),
        ('type', ctypes.c_uint8), ('subtype', ctypes.c_uint8), ('pkg_id', ctypes.c_uint16),
    ]


def is_tag_hash(value):
    """True if the value has the form of a package entry hash."""
    return 0x80800000 < value <= 0x81FFFFFF and 0x9 <= ((value - 0x80800000) >> 13) < 0xA00


class PackageManager:
    """Read-only view of all packages of one game installation."""

    def __init__(self, packages=None, version=None, library=None, runtime=None):
        self.packages = Path(packages or default_packages())
        self.version = version or DEFAULT_VERSION
        library = Path(library or DEFAULT_LIBRARY)
        if not library.is_file():
            raise FileNotFoundError(f'{library} is missing. {SETUP_HINT}')
        if not self.packages.is_dir():
            raise FileNotFoundError(f'The packages folder {self.packages} is missing. Give the game folder in the '
                                    'setting `destiny_game` (data/config.toml or D2X_GAME), or use --packages.')
        runtime = Path(runtime or DEFAULT_RUNTIME)
        lib = ctypes.CDLL(str(library))
        lib.tp_open.restype = ctypes.c_void_p
        lib.tp_open.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p]
        lib.tp_close.argtypes = [ctypes.c_void_p]
        lib.tp_entry.restype = ctypes.c_int32
        lib.tp_entry.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(_Entry)]
        lib.tp_read.restype = ctypes.c_void_p
        lib.tp_read.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.POINTER(ctypes.c_uint64)]
        lib.tp_free.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        lib.tp_list.restype = ctypes.c_void_p
        lib.tp_list.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_uint64)]
        lib.tp_free_list.argtypes = [ctypes.c_void_p, ctypes.c_uint64]
        lib.tp_pkg_name.restype = ctypes.c_int32
        lib.tp_pkg_name.argtypes = [ctypes.c_void_p, ctypes.c_uint16, ctypes.c_char_p, ctypes.c_uint64]
        self._lib = lib
        self._handle = lib.tp_open(str(self.packages).encode(), self.version.encode(), str(runtime).encode())
        if not self._handle:
            raise RuntimeError(f'Could not open packages at {self.packages} as {self.version}')
        self._entries = None
        self._index = None
        self._cache = {}

    def close(self):
        if self._handle:
            self._lib.tp_close(self._handle)
            self._handle = None

    @property
    def entries(self):
        """All package entries as a structured numpy array, sorted by tag."""
        if self._entries is None:
            count = ctypes.c_uint64()
            pointer = self._lib.tp_list(self._handle, ctypes.byref(count))
            raw = ctypes.string_at(pointer, count.value * ENTRY_DTYPE.itemsize)
            self._lib.tp_free_list(pointer, count)
            self._entries = np.frombuffer(raw, dtype=ENTRY_DTYPE)
            # Contiguous copy: a field view would be copied on every search.
            self._tags = np.ascontiguousarray(self._entries['tag'])
        return self._entries

    def entry(self, tag):
        """Entry record (numpy void) for a tag, or None."""
        entries = self.entries
        index = int(np.searchsorted(self._tags, tag))
        if index < len(entries) and self._tags[index] == tag:
            return entries[index]
        return None

    def reference(self, tag):
        """Class hash (or parent entry) of a tag; 0 if the tag is unknown."""
        entry = self.entry(tag)
        return int(entry['reference']) if entry is not None else 0

    def exists(self, tag):
        return self.entry(tag) is not None

    def read(self, tag, cache=True):
        """Decrypted and decompressed data of one entry."""
        if cache and tag in self._cache:
            return self._cache[tag]
        length = ctypes.c_uint64()
        pointer = self._lib.tp_read(self._handle, tag, ctypes.byref(length))
        if not pointer:
            raise KeyError(f'Could not read tag {tag:08X}')
        data = ctypes.string_at(pointer, length.value)
        self._lib.tp_free(pointer, length)
        if cache:
            self._cache[tag] = data
        return data

    def by_reference(self, reference):
        """All tags whose class hash is `reference`."""
        entries = self.entries
        return entries['tag'][entries['reference'] == reference].tolist()

    def by_type(self, file_type, subtype=None):
        entries = self.entries
        mask = entries['type'] == file_type
        if subtype is not None:
            mask &= entries['subtype'] == subtype
        return entries['tag'][mask].tolist()

    def pkg_name(self, tag_or_pkg_id):
        pkg_id = tag_or_pkg_id if tag_or_pkg_id < 0x10000 else (tag_or_pkg_id - 0x80800000) >> 13
        buffer = ctypes.create_string_buffer(256)
        count = self._lib.tp_pkg_name(self._handle, pkg_id, buffer, 256)
        return buffer.raw[:count].decode() if count >= 0 else '?'

    def clear_cache(self):
        self._cache.clear()


_shared = None


def shared():
    """Process-wide PackageManager with the default settings."""
    global _shared
    if _shared is None:
        _shared = PackageManager()
    return _shared
