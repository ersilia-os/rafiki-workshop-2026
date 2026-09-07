"""Write the SMILES files handed to each group.

One file per library, SMILES only and shuffled, so a group gets a plain list of
compounds with no predictions attached. The app matches an uploaded file back to
its library by SMILES overlap.
"""

import os

import pandas as pd

RANDOM_SEED = 42
SMILES_COLUMN = "input"

root = os.path.dirname(os.path.abspath(__file__))
data_dir = os.path.join(root, "..", "data")
output_dir = os.path.join(data_dir, "group_inputs")
os.makedirs(output_dir, exist_ok=True)

for i in range(1, 7):
    source = os.path.join(data_dir, "library_{0}.csv".format(i))
    df = pd.read_csv(source).sample(frac=1, random_state=RANDOM_SEED)
    target = os.path.join(output_dir, "group_{0}.csv".format(i))
    df[[SMILES_COLUMN]].rename(columns={SMILES_COLUMN: "smiles"}).to_csv(target, index=False)
    print("group_{0}.csv  {1} compounds".format(i, len(df)))
