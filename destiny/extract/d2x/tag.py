"""Binary reader for Tiger engine tag data (little-endian, 64-bit layouts)."""
import struct

import numpy as np


class Reader:
    """Random-access reader over one tag's bytes."""

    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def u8(self, offset):
        return self.data[offset]

    def u16(self, offset):
        return struct.unpack_from('<H', self.data, offset)[0]

    def i16(self, offset):
        return struct.unpack_from('<h', self.data, offset)[0]

    def u32(self, offset):
        return struct.unpack_from('<I', self.data, offset)[0]

    def i32(self, offset):
        return struct.unpack_from('<i', self.data, offset)[0]

    def u64(self, offset):
        return struct.unpack_from('<Q', self.data, offset)[0]

    def i64(self, offset):
        return struct.unpack_from('<q', self.data, offset)[0]

    def f32(self, offset):
        return struct.unpack_from('<f', self.data, offset)[0]

    def floats(self, offset, count):
        return struct.unpack_from(f'<{count}f', self.data, offset)

    def rel(self, offset):
        """Target of a relative pointer stored at `offset` (0 if null)."""
        value = self.i64(offset)
        return offset + value if value else 0

    def array(self, offset):
        """Dynamic array field at `offset`: returns (count, data offset, element class).

        Field layout: u64 count, i64 relative pointer. The pointer leads to a
        16-byte block header (u64 count, u32 class, u32 pad) followed by data.
        """
        count = self.u64(offset)
        if count == 0:
            return 0, 0, 0
        header = self.rel(offset + 8)
        if header <= 0 or header + 16 > len(self.data):
            return 0, 0, 0
        return count, header + 16, self.u32(header + 8)

    def array_items(self, offset, stride):
        """Offsets of the elements of the dynamic array field at `offset`."""
        count, start, _ = self.array(offset)
        return [start + i * stride for i in range(count)]

    def np_array(self, offset, dtype):
        count, start, _ = self.array(offset)
        return np.frombuffer(self.data, dtype=dtype, count=count, offset=start) if count else np.zeros(0, dtype)

    def cstring(self, offset):
        end = self.data.index(b'\0', offset)
        return self.data[offset:end].decode('utf-8', 'replace')


def fnv1(text):
    """FNV-1 32-bit hash that the engine uses for names."""
    value = 0x811C9DC5
    for byte in text.encode():
        value = ((value * 0x01000193) & 0xFFFFFFFF) ^ byte
    return value


def hexdump(data, start=0, length=0x100, width=16):
    lines = []
    for offset in range(start, min(len(data), start + length), width):
        chunk = data[offset:offset + width]
        text = ' '.join(f'{b:02X}' for b in chunk)
        lines.append(f'{offset:06X}  {text}')
    return '\n'.join(lines)
