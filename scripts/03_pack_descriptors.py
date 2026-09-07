"""Convert the raw Ersilia featuriser CSVs into the files the app reads.

Descriptor matrices become float32 .npy: a 10,000 x 2048 matrix is ~82 MB as
.npy against ~300 MB as CSV, and loads in a fraction of the time. The eos1klk
projection stays a CSV, since it is only 8 columns.

Row order must match data/saureus.csv exactly, because the app pairs each row
with a label by position. This script checks that rather than assuming it.
"""

import os

import numpy as np
import pandas as pd

DESCRIPTOR_MODELS = ["eos4wt0", "eos9o72"]
PROJECTION_MODEL = "eos1klk"
ID_COLUMNS = ["key", "input", "smiles"]

root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(root, "..", "data")

reference = pd.read_csv(os.path.join(data_dir, "saureus.csv"))

for model in DESCRIPTOR_MODELS + [PROJECTION_MODEL]:
    source = os.path.join(data_dir, "saureus_{0}.csv".format(model))
    if not os.path.exists(source):
        print("{0}: missing {1}, skipping".format(model, os.path.basename(source)))
        continue

    df = pd.read_csv(source)
    assert len(df) == len(reference), "{0}: {1} rows, expected {2}".format(
        model, len(df), len(reference))
    if "input" in df.columns:
        mismatched = (df["input"].values != reference["smiles"].values).sum()
        assert mismatched == 0, "{0}: {1} rows out of order".format(model, mismatched)

    features = [c for c in df.columns if c not in ID_COLUMNS]

    if model == PROJECTION_MODEL:
        target = os.path.join(data_dir, "saureus_{0}.csv".format(model))
        df[features].to_csv(target, index=False)
        print("{0}: kept {1} projection columns as CSV".format(model, len(features)))
    else:
        X = df[features].to_numpy(dtype=np.float32)
        if np.isin(X, (0.0, 1.0)).all():
            X = X.astype(np.uint8)  # binary fingerprints: a quarter of the size
        target = os.path.join(data_dir, "saureus_{0}.npy".format(model))
        np.save(target, X)
        print("{0}: {1} {2} -> {3:.0f} MB".format(
            model, X.shape, X.dtype, os.path.getsize(target) / 1e6))
