import os

# Everything that changes between workshop editions lives in this file.

TITLE = "Rafiki Workshop 2026"
PAGE_ICON = ":microbe:"

about = [
    "This app is part of the Rafiki Workshop 2026.",
    "It has been developed by the [Ersilia Open Source Initiative](https://ersilia.io).",
    "Code and data are available in this [GitHub repository](https://github.com/ersilia-os/rafiki-workshop-2026).",
    "If you have a use case for your own research, contact us at [hello@ersilia.io](mailto:hello@ersilia.io).",
]

intro = """
Your collaborators have screened a compound library against _Staphylococcus aureus_ ATCC 29213 and
handed you the raw numbers. Each compound was tested once at 50 uM, in duplicate, and the result is
reported as **mean % growth inhibition**: 100% means the bacteria did not grow at all, 0% means they
grew as well as in an untreated well. Your job today is to turn these measurements into a machine
learning model that can flag promising compounds in libraries you have not screened.
""".strip()

# --- Training data -----------------------------------------------------------
# CSV in data/, built by scripts/01_prepare_saureus_dataset.py.
TRAINING_FILE = "saureus.csv"
SMILES_COLUMN = "smiles"
READOUT_COLUMN = "growth_inhibition"
READOUT_LABEL = "Growth inhibition (%)"

# True if a HIGH readout means an active compound (e.g. % inhibition),
# False if a LOW readout means active (e.g. optical density of bacterial growth).
HIGHER_IS_ACTIVE = True

# Slider bounds for the activity cut-off, in the units of READOUT_COLUMN.
CUTOFF_MIN, CUTOFF_MAX, CUTOFF_DEFAULT, CUTOFF_STEP = 0.0, 100.0, 50.0, 0.5

# --- Precomputed featurisations ---------------------------------------------
# One compressed .npz per descriptor, in data/, rows in the same order as
# TRAINING_FILE. Produced offline: scripts/02_run_featurisers.sh then
# scripts/03_pack_descriptors.py.
DESCRIPTORS = {
    "Morgan fingerprints": "saureus_eos4wt0.npz",   # eos4wt0, 2048 binary bits
    "CheMeleon embeddings": "saureus_eos9o72.npz",  # eos9o72, 2048-d foundation model
}

# 2D projection onto Ersilia's reference chemical space (eos1klk). Small enough
# to stay a CSV; columns are pca_x/y, tmap_x/y, tsne_x/y, umap_x/y.
PROJECTION_FILE = "saureus_eos1klk.csv"
PROJECTION_X, PROJECTION_Y = "umap_x", "umap_y"

# --- Screening libraries -----------------------------------------------------
# Each group is handed a SMILES file matching one of these. Predictions are
# already computed; the app matches the upload to a library by SMILES overlap.
LIBRARY_FILES = [
    "library_1.csv", "library_2.csv", "library_3.csv",
    "library_4.csv", "library_5.csv", "library_6.csv",
]
LIBRARY_SMILES_COLUMN = "input"

# Handout files written by scripts/04_make_group_inputs.py. The app offers
# one for download so the upload step can be demoed without a local file.
EXAMPLE_INPUT = os.path.join("group_inputs", "group_1.csv")

# The two S. aureus activity predictions shown first.
ACTIVITY_MODELS = {
    "EU-OpenScreen model": "eos3f8h_saureus",
    "ChEMBL model": "eos8lcw_consensus_score",
}

# The rest of the array, shown in the final downloadable table.
COLUMN_LABELS = {
    "eos42ez_cytotoxicity_hepg2": "Cytotoxicity HepG2",
    "eos7d58_herg": "hERG inhibition",
    "eos9ei3_sa_score": "Synthetic accessibility",
    "eos9yui_np_score": "Natural product likeness",
    "eos2xeq_has_pains": "PAINS alert",
    "eos2xeq_has_brenk": "Brenk alert",
    "eos2xeq_is_sim_known_ab": "Similar to known antibiotic",
    "eos4djh_fsp3": "Fsp3",
    "eos4djh_clogp": "cLogP",
    "eos4djh_qed": "QED",
}

N_TOP_HITS = 8

# --- Discussion questions ----------------------------------------------------
q1 = [
    "- What does each row represent?",
    "- What exactly was measured, and in what units?",
    "- Do we want higher or lower values?",
    "- Some values are negative, and some are above 100. How can that be?",
    "- What information would you ask your collaborators for that is missing here?",
]

q2 = [
    "- Why do we need a cut-off at all, when we already have numbers?",
    "- What do 0 and 1 mean once we binarise?",
    "- Where does the cut-off sit on the histogram, and what does the tail contain?",
    "- The depositors called a compound active at 70% inhibition. Would you?",
    "- Is this dataset balanced? Careful: all the actives were kept and the",
    "  inactives were downsampled, so the hit rate you see here is about ten",
    "  times higher than in the original screen.",
]

q3 = [
    "- What does a Morgan fingerprint encode? And a learned embedding?",
    "- One is a fixed rule, the other was trained. Does that matter here?",
    "- Look at the two example rows: what is actually being fed to the model?",
    "- What is a cross-validation experiment, and why do we need one?",
    "- Which descriptor performs better? Is the difference meaningful?",
    "- Would a different cut-off change the ranking?",
]

q4 = [
    "- The two models were trained on different data. Do they agree?",
    "- Which compounds would you take forward, and on whose prediction?",
    "- What does a score of 0.9 actually mean here?",
]

q5 = [
    "- Activity is not enough. What else in this table would stop you?",
    "- A compound is predicted active but flags PAINS. What now?",
    "- You can synthesise 50 compounds. Which 50, and why?",
]
