#!/usr/bin/env python3
"""Problem-anchored collide: sample real domains FAR from an anchor text.

Reuses itch's collide corpus (~17k real arXiv/OpenAlex/HF/GitHub/Wikipedia
domains, bge-small embedded) and its temperature-banded farthest-point
sampler -- but anchors on an ARBITRARY problem statement instead of Avi's
interest profile. Purpose: hand the excavator domains structurally distant
from "MoE quantization" so it can borrow a mechanism from a far field and
build its way back. Chaos, not noise: every domain is a real published field.

Usage:
  collide_blend.py --anchor "the problem text" --temp 0.85 --k 4
Output (stdout): JSON list of {title, source, cos_dist, rank}
"""
import argparse, json, os, sys, random
import numpy as np

ITCH = os.path.expanduser("~/projects/itch")
sys.path.insert(0, ITCH)
# reuse itch's own loaders + sampler so behavior matches the proven tool
import collide_sample as cs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--anchor", required=True, help="problem text to sample AWAY from")
    ap.add_argument("--temp", type=float, default=0.85, help="0..1; high=far from anchor")
    ap.add_argument("--k", type=int, default=4)
    A = ap.parse_args()
    temp = max(0.0, min(1.0, A.temp))

    seeds, titles = cs._load_partial_index()          # (N,384) real-domain embeds
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(cs._bge_path(), device=cs._device())
    # anchor takes the place of interest bullets: one vector = the problem
    V = model.encode([A.anchor], normalize_embeddings=True).astype("float32")

    rng = random.Random(int.from_bytes(os.urandom(4), "little"))
    idx, dist, rank, _ = cs.collide_sample(V, seeds, temp, A.k, rng, titles=titles)
    out = [{
        "title": titles[i]["title"],
        "source": titles[i].get("source", ""),
        "cos_dist": float(dist[j]),
        "rank": float(rank[j]),
    } for j, i in enumerate(idx)]
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
