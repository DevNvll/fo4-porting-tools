"""Read files from a Fallout 4 archive (.ba2) of the general kind.

    python3 tools/ba2.py ARCHIVE [PATTERN]        list the files whose name has PATTERN

A general archive (type GNRL) has a header, one record for each file and a table of names.
A file is stored as it is or with zlib compression. A texture archive (type DX10) is a
different kind, and this reader refuses it.
"""
import struct
import sys
import zlib


class Ba2:
    def __init__(self, path):
        self.path = path
        self.file = open(path, 'rb')
        magic, version, kind, count, names = struct.unpack('<4sI4sIQ', self.file.read(24))
        if magic != b'BTDX' or kind != b'GNRL':
            raise SystemExit('%s is not a general Fallout 4 archive (BTDX, GNRL)' % path)
        if version in (2, 3):
            # a later version of the format has 8 or 12 more bytes in the header
            self.file.read(8 if version == 2 else 12)
        self.records = [struct.unpack('<I4sIIQIII', self.file.read(36)) for _ in range(count)]
        self.file.seek(names)
        self.names = []
        for _ in range(count):
            size, = struct.unpack('<H', self.file.read(2))
            self.names.append(self.file.read(size).decode('utf-8', 'replace').replace('\\', '/'))
        self.index = {n.lower(): i for i, n in enumerate(self.names)}

    def find(self, prefix, suffix=''):
        """The names that start with a folder path and end with a suffix, with no regard to case."""
        prefix, suffix = prefix.replace('\\', '/').lower(), suffix.lower()
        return [n for n in self.names if n.lower().startswith(prefix) and n.lower().endswith(suffix)]

    def read(self, name):
        i = self.index.get(name.replace('\\', '/').lower())
        if i is None:
            raise SystemExit('%s has no file %s' % (self.path, name))
        _, _, _, _, offset, packed, size, _ = self.records[i]
        self.file.seek(offset)
        if packed:
            data = zlib.decompress(self.file.read(packed))
        else:
            data = self.file.read(size)
        if len(data) != size:
            raise SystemExit('%s: %s has %d bytes, the archive says %d' % (self.path, name, len(data), size))
        return data


if __name__ == '__main__':
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    archive = Ba2(sys.argv[1])
    word = sys.argv[2].lower() if len(sys.argv) > 2 else ''
    for n in archive.names:
        if word in n.lower():
            print(n)
