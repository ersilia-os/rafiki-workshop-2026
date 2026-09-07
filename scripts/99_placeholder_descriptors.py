"""TEMPORARY. Writes FAKE descriptor and projection files so the app can be
laid out and demoed before the real Ersilia featurisers finish.

The numbers here are random. They are shaped like the real outputs — same row
count, same dimensions, same column names — and they are made mildly predictive
so the ROC curve is not a straight diagonal. Nothing about them is chemistry.

Never show these to participants and never commit them. Running
02_run_featurisers.sh then 03_pack_descriptors.py overwrites every file this
script creates. Delete data/.placeholder when the real files are in place; the
app reads that marker to show a warning banner.
"""

import os

import numpy as np
import pandas as pd

RANDOM_SEED = 0
N_BITS = 2048

root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(root, "..", "data")

df = pd.read_csv(os.path.join(data_dir, "saureus.csv"))
n = len(df)
active = (df["growth_inhibition"] >= 50).to_numpy()
rng = np.random.default_rng(RANDOM_SEED)

written = []

# eos4wt0: sparse binary bits, a handful of them enriched in the actives
morgan = (rng.random((n, N_BITS)) < 0.03).astype(np.uint8)
signal = rng.choice(N_BITS, 40, replace=False)
morgan[np.ix_(active, signal)] = (rng.random((active.sum(), 40)) < 0.55).astype(np.uint8)
np.savez_compressed(os.path.join(data_dir, "saureus_eos4wt0.npz"), features=morgan)
written.append("saureus_eos4wt0.npz")

# eos9o72: dense float embedding, actives shifted along a few directions
chemeleon = rng.normal(size=(n, N_BITS)).astype(np.float16)
chemeleon[active] += rng.normal(0.35, 0.1, N_BITS).astype(np.float16)
np.savez_compressed(os.path.join(data_dir, "saureus_eos9o72.npz"), features=chemeleon)
written.append("saureus_eos9o72.npz")

# eos1klk: 8 projection columns, a few blobs so the map is not a gaussian cloud
centres = rng.normal(0, 6, size=(8, 2))
assignment = rng.integers(0, len(centres), n)
projection = {}
for method in ("pca", "tmap", "tsne", "umap"):
    offset = rng.normal(0, 3, size=2)
    xy = centres[assignment] + rng.normal(0, 1.1, size=(n, 2)) + offset
    xy[active] += rng.normal(1.5, 0.5, size=(active.sum(), 2))
    projection[method + "_x"], projection[method + "_y"] = xy[:, 0], xy[:, 1]
pd.DataFrame(projection).to_csv(os.path.join(data_dir, "saureus_eos1klk.csv"), index=False)
written.append("saureus_eos1klk.csv")

with open(os.path.join(data_dir, ".placeholder"), "w") as f:
    f.write("\n".join(written) + "\n")

for name in written:
    size = os.path.getsize(os.path.join(data_dir, name)) / 1e6
    print("FAKE  {0:<28} {1:>6.1f} MB".format(name, size))
