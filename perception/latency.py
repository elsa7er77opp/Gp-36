"""Latency statistics (p50 / p95 / p99) for the stream log."""
import numpy as np


def summarize(values_ms):
    v = np.asarray([x for x in values_ms if x is not None], dtype=float)
    if v.size == 0:
        return {"n": 0}
    return {"n": int(v.size), "mean": round(float(v.mean()), 2),
            "p50": round(float(np.percentile(v, 50)), 2),
            "p95": round(float(np.percentile(v, 95)), 2),
            "p99": round(float(np.percentile(v, 99)), 2),
            "max": round(float(v.max()), 2)}
