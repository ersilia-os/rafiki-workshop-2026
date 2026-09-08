"""Give every compound in the six libraries a stable RAFIKI identifier.

Writes data/rafiki_ids.csv, two columns: rafiki_id, smiles.

The identifiers are assigned here, once, and committed - not generated in the
app. An app that numbered compounds at runtime would renumber them whenever the
data or the iteration order changed, and a participant's "RAFIKI-0421" would
stop meaning anything between sessions.

Reproducibility
    The union of SMILES is sorted before it is shuffled. Set iteration order in
    Python depends on PYTHONHASHSEED, so shuffling a set directly would hand out
    different identifiers on different runs even with the seed fixed. Sorting
    first makes the input to the shuffle deterministic, and the seed then makes
    the shuffle deterministic, so re-running this script reproduces the file
    exactly.

Note on platensimycin
    It appears in all six libraries, which is why the union is 5,995 rather than
    6,000. The library copies carry no stereochemistry, so they do NOT match
    info.PARENT_SMILES as strings - that one has all six stereocentres assigned.
    Match on the flattened form if you need to find it.
"""

import os
import random

import pandas as pd

RANDOM_SEED = 42
ID_FORMAT = "RAFIKI-{0:04d}"
SMILES_COLUMN = "input"
LIBRARIES = ["library_{0}.csv".format(i) for i in range(1, 7)]

root = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(root, "..", "data")
OUTPUT = os.path.join(DATA, "rafiki_ids.csv")

smiles = []
for name in LIBRARIES:
    column = pd.read_csv(os.path.join(DATA, name))[SMILES_COLUMN]
    print("{0:<16} {1:5d} rows".format(name, len(column)))
    smiles += list(column)

unique = sorted(set(smiles))
print("\n{0} rows, {1} unique compounds ({2} duplicated across libraries)".format(
    len(smiles), len(unique), len(smiles) - len(unique)))

random.Random(RANDOM_SEED).shuffle(unique)

table = pd.DataFrame({
    "rafiki_id": [ID_FORMAT.format(i + 1) for i in range(len(unique))],
    "smiles": unique,
})
table.to_csv(OUTPUT, index=False)
print("wrote {0} to {1}".format(
    " to ".join([table["rafiki_id"].iloc[0], table["rafiki_id"].iloc[-1]]),
    os.path.relpath(OUTPUT, root),
))
