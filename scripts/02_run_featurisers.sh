#!/bin/bash
# Run the Ersilia featurisers over data/saureus.csv. Outputs raw CSVs which
# 03_pack_descriptors.py then converts to the .npy files the app reads.
# Run from the repository root, in the ersilia conda environment.

set -e

INPUT=data/saureus_smiles.csv

# Ersilia wants a plain list of SMILES, not the readout column alongside it.
python -c "import pandas as pd; pd.read_csv('data/saureus.csv')[['smiles']].to_csv('$INPUT', index=False)"

# eos4wt0  Morgan fingerprints, binary, radius 3, 2048 bits
# eos9o72  CheMeleon embeddings, 2048-d molecular foundation model
# eos1klk  2D projections (PCA/UMAP/t-SNE/TMAP) onto Ersilia's reference library
for MODEL in eos4wt0 eos9o72 eos1klk; do
    ersilia -v fetch "$MODEL"
    ersilia -v serve "$MODEL"
    ersilia -v run -i "$INPUT" -o "data/saureus_${MODEL}.csv"
    ersilia close
done
