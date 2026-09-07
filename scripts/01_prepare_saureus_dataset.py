"""Build data/saureus.csv, the training set the workshop app reads.

Source
    eu-openscreen-antimicrobial-tasks/data/raw/00_extracted_assays/EOS300078.csv
    EU-OpenScreen ECBD assay "MSSA ATCC 29213 Anti-Bacterial Assay": S. aureus
    ATCC 29213, single point 50 uM, 2 replicates, 384-well, absorbance readout.
    Snapshot: file mtime 2026-07-30 (the ECBD dump carries no other version).
    The `value` column is mean % growth inhibition; 100% is total inhibition of
    bacterial growth and 0% is full growth, so a HIGH value means an ACTIVE
    compound.

Composition of the 10,000 shipped rows
    all 379 actives          value >= 70   (the depositor's own threshold)
    all 242 inconclusive     50 <= value < 70
    9,379 inactives          value < 50, sampled with RANDOM_SEED

    156 source rows have no `value` and are dropped: they cannot be binarised at
    any cut-off the student might choose.

Caveat that must be stated in the room
    The hit rate here is inflated roughly 10x. Every active was kept while the
    inactives were downsampled, so actives are 3.8% of this file at a cut-off of
    70 against 0.375% in the real 101,024-compound screen. This is a teaching
    set: it is not a basis for any statement about how often a screen hits.
"""

import os

import pandas as pd
from rdkit import Chem, RDLogger

RDLogger.DisableLog("rdApp.*")

RANDOM_SEED = 42
N_TOTAL = 10000
ACTIVE_CUTOFF = 70
INCONCLUSIVE_CUTOFF = 50

root = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(
    root, "..", "..", "eu-openscreen-antimicrobial-tasks",
    "data", "raw", "00_extracted_assays", "EOS300078.csv",
)
OUTPUT = os.path.join(root, "..", "data", "saureus.csv")


def canonical(smiles):
    mol = Chem.MolFromSmiles(smiles)
    return None if mol is None else Chem.MolToSmiles(mol)


df = pd.read_csv(SOURCE)
print("source rows:", len(df))

df = df[df["value"].notna()]
print("dropped for missing value:", 101024 - len(df))

actives = df[df["value"] >= ACTIVE_CUTOFF]
inconclusive = df[(df["value"] >= INCONCLUSIVE_CUTOFF) & (df["value"] < ACTIVE_CUTOFF)]
inactives = df[df["value"] < INCONCLUSIVE_CUTOFF]
n_sample = N_TOTAL - len(actives) - len(inconclusive)
print("actives {0}, inconclusive {1}, inactives sampled {2} of {3}".format(
    len(actives), len(inconclusive), n_sample, len(inactives)))

subset = pd.concat([actives, inconclusive, inactives.sample(n_sample, random_state=RANDOM_SEED)])
subset = subset.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)

subset["smiles"] = [canonical(s) for s in subset["smiles"]]
n_unparseable = subset["smiles"].isna().sum()
subset = subset[subset["smiles"].notna()]
print("dropped for unparseable SMILES:", n_unparseable)
print("duplicate SMILES kept:", int(subset["smiles"].duplicated().sum()))

subset = subset.rename(columns={"value": "growth_inhibition"})
subset[["smiles", "growth_inhibition"]].to_csv(OUTPUT, index=False)
print("wrote {0} rows to {1}".format(len(subset), os.path.relpath(OUTPUT, root)))
