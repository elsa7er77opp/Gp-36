"""Duplicate and leakage-group discovery.

Samples are linked (union-find) when they are
  * byte-identical (same SHA-256),
  * perceptually near-identical (dHash <= dhash_max AND pHash <= phash_max), or
  * declared related by metadata (same ``group_key``, e.g. one video, or one Roboflow source stem).
Every connected component is one leakage group: it must never be split across partitions.
"""
from collections import defaultdict

import numpy as np

from .hashing import hamming_to_all


class UnionFind:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, a):
        while self.parent[a] != a:
            self.parent[a] = self.parent[self.parent[a]]
            a = self.parent[a]
        return a

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.parent[max(ra, rb)] = min(ra, rb)


def find_links(samples, dhash_max=4, phash_max=10):
    """Return a list of (i, j, reason, dhash_dist, phash_dist) links between sample indices.

    samples: sequence of dicts with keys sha256, dhash, phash and optional group_key.
    """
    links = []
    by_sha = defaultdict(list)
    by_key = defaultdict(list)
    for i, s in enumerate(samples):
        by_sha[s["sha256"]].append(i)
        if s.get("group_key"):
            by_key[s["group_key"]].append(i)
    for idx in by_sha.values():
        links += [(idx[0], j, "exact", 0, 0) for j in idx[1:]]
    for idx in by_key.values():
        links += [(idx[0], j, "metadata", -1, -1) for j in idx[1:]]
    D = np.array([s["dhash"] for s in samples], dtype=np.uint64)
    P = np.array([s["phash"] for s in samples], dtype=np.uint64)
    for i in range(len(samples) - 1):
        dd = hamming_to_all(int(D[i]), D[i + 1:])
        cand = np.nonzero(dd <= dhash_max)[0]
        if len(cand) == 0:
            continue
        pd = hamming_to_all(int(P[i]), P[i + 1 + cand])
        for c, p in zip(cand, pd):
            j = i + 1 + int(c)
            if p <= phash_max and samples[i]["sha256"] != samples[j]["sha256"]:
                links.append((i, j, "near", int(dd[c]), int(p)))
    return links


def group_samples(samples, links):
    """Return a list of group ids (smallest member index of each component)."""
    uf = UnionFind(len(samples))
    for i, j, *_ in links:
        uf.union(i, j)
    return [uf.find(i) for i in range(len(samples))]
