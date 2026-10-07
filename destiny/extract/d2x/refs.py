"""Reference index: which structured tag (type 8) points at which entry.

The index is built once per game installation and cached in data/destiny/extract/out/cache.
"""
import time
from pathlib import Path

import numpy as np

from .pkg import DEFAULT_OUT

CACHE = DEFAULT_OUT / 'cache'


class ReferenceIndex:
    def __init__(self, pm, rebuild=False):
        self.pm = pm
        path = CACHE / f'refs_{pm.version}.npz'
        if path.is_file() and not rebuild:
            loaded = np.load(path)
            self.src, self.dst = loaded['src'], loaded['dst']
        else:
            self.src, self.dst = self._build()
            CACHE.mkdir(parents=True, exist_ok=True)
            np.savez(path, src=self.src, dst=self.dst)
        # `src`/`dst` are sorted by src; a second ordering gives reverse lookups.
        self._by_dst = np.argsort(self.dst, kind='stable')
        self._dst_sorted = self.dst[self._by_dst]

    def _build(self):
        pm = self.pm
        entries = pm.entries
        all_tags = entries['tag']
        tags = all_tags[entries['type'] == 8]
        src_parts, dst_parts = [], []
        started = time.time()
        for number, tag in enumerate(tags):
            tag = int(tag)
            try:
                data = pm.read(tag, cache=False)
            except KeyError:
                continue
            usable = len(data) & ~3
            if usable < 4:
                continue
            words = np.frombuffer(data, dtype='<u4', count=usable // 4)
            candidates = words[(words > 0x80812000) & (words <= 0x81FFFFFF)]
            if len(candidates) == 0:
                continue
            candidates = np.unique(candidates)
            positions = np.searchsorted(all_tags, candidates)
            positions[positions >= len(all_tags)] = 0
            found = candidates[all_tags[positions] == candidates]
            found = found[found != tag]
            if len(found):
                src_parts.append(np.full(len(found), tag, dtype='<u4'))
                dst_parts.append(found)
            if number % 200000 == 0:
                print(f'  reference index: {number}/{len(tags)} tags, {time.time() - started:.0f} s', flush=True)
        return np.concatenate(src_parts), np.concatenate(dst_parts)

    def targets(self, tag):
        """Entries that `tag` points at."""
        low = np.searchsorted(self.src, tag, 'left')
        high = np.searchsorted(self.src, tag, 'right')
        return self.dst[low:high].tolist()

    def sources(self, tag):
        """Structured tags that point at `tag`."""
        low = np.searchsorted(self._dst_sorted, tag, 'left')
        high = np.searchsorted(self._dst_sorted, tag, 'right')
        return self.src[self._by_dst[low:high]].tolist()
