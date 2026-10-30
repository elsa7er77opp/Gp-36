"""Deterministic, group-aware train/val/test assignment.

Whole groups are assigned to one split. The cost of an assignment is a chi-square-style distance
between each split's share and its target ratio, summed over the image count and every per-class
object count (so the dimensions cannot cancel each other out):

    cost = sum_split sum_dim (share - ratio)^2 / ratio

A greedy pass (largest groups first, ties broken by a seeded hash of the group id) gives a start,
then single-group moves are applied while they lower the cost. The result depends only on the
inputs and the seed.
"""
import hashlib


def _tiebreak(seed, gid):
    return hashlib.sha256(f"{seed}:{gid}".encode()).hexdigest()


def group_split(groups, ratios=None, seed=0, forced=None, max_passes=50):
    """Assign each group to a split.

    groups: {gid: {"n": n_images, "classes": {class_id: n_objects}}}
    ratios: {split_name: fraction}, fractions sum to 1 (default 70/20/10 train/val/test)
    forced: {gid: split_name} for groups whose split is decided by policy (e.g. a held-out video);
            forced groups are excluded from the balancing.
    Returns {gid: split_name}.
    """
    ratios = ratios or {"train": 0.7, "val": 0.2, "test": 0.1}
    if abs(sum(ratios.values()) - 1) > 1e-9:
        raise ValueError("ratios must sum to 1")
    forced = forced or {}
    unknown = set(forced) - set(groups)
    if unknown:
        raise KeyError(f"forced groups not found: {sorted(unknown)[:5]}")
    bad = {s for s in forced.values() if s not in ratios and s != "holdout"}
    if bad:
        raise ValueError(f"forced to unknown split(s): {bad}")

    splits = list(ratios)
    free = [g for g in groups if g not in forced]
    classes = sorted({c for g in free for c in groups[g]["classes"]})

    def vec(g):
        return [groups[g]["n"]] + [groups[g]["classes"].get(c, 0) for c in classes]

    V = {g: vec(g) for g in free}
    totals = [sum(V[g][k] for g in free) for k in range(len(classes) + 1)]
    have = {s: [0] * len(totals) for s in splits}

    def split_cost(s, h):
        r = ratios[s]
        return sum((x / t - r) ** 2 / r for x, t in zip(h, totals) if t)

    def delta_add(s, v, sign=1):
        h = have[s]
        return split_cost(s, [a + sign * b for a, b in zip(h, v)]) - split_cost(s, h)

    def apply(s, v, sign=1):
        have[s] = [a + sign * b for a, b in zip(have[s], v)]

    order = sorted(free, key=lambda g: (-groups[g]["n"], _tiebreak(seed, g)))
    assign = {}
    for g in order:
        s = min(splits, key=lambda s: (delta_add(s, V[g]), splits.index(s)))
        assign[g] = s
        apply(s, V[g])

    for _ in range(max_passes):
        improved = False
        for g in order:
            cur = assign[g]
            leave = delta_add(cur, V[g], -1)
            best, best_d = cur, -1e-12
            for s in splits:
                if s != cur:
                    d = leave + delta_add(s, V[g])
                    if d < best_d:
                        best, best_d = s, d
            if best != cur:
                apply(cur, V[g], -1)
                apply(best, V[g])
                assign[g] = best
                improved = True
        if not improved:
            break
    return {**assign, **forced}
