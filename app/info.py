import os

# Everything that changes between workshop editions lives in this file.

TITLE = "RAFIKI Workshop 2026"
# Sits beside the Ersilia wordmark in the header, in place of a sidebar.
WORDMARK_LABEL = "RAFIKI Workshop, Nairobi, 2026"
WORKSHOP_URL = "https://ersilia.gitbook.io/ersilia-workshops/rafiki"
ORGANISATION = "Ersilia Open Source Initiative"

# The top navigation: url_path, tab label, icon, and the function in steps.py.
PAGES = [
    ("data", "Data", ":material/table:", "understand_the_data"),
    ("train", "Train", ":material/model_training:", "train_a_model"),
    ("screen", "Screen", ":material/search:", "screen_a_library"),
    ("profiling", "Profiling", ":material/list_alt:", "the_full_picture"),
    ("collective", "Collective", ":material/groups:", "collective_picks"),
    ("expand", "Expand", ":material/hub:", "hit_expansion"),
]

about = [
    "This app is part of the RAFIKI Workshop 2026.",
    "It has been developed by the [Ersilia Open Source Initiative](https://ersilia.io).",
    "Code and data are available in this [GitHub repository](https://github.com/ersilia-os/rafiki-workshop-2026).",
    "If you have a use case for your own research, contact us at [hello@ersilia.io](mailto:hello@ersilia.io).",
]

intro = """
Public screening data from EU-OPENSCREEN: a compound library tested against
_Staphylococcus aureus_ ATCC 29213 at 50 uM, in duplicate. The readout is
**mean % growth inhibition** - 100% means the bacteria did not grow at all, 0% means
they grew as well as in an untreated well. Over five steps you will turn these
measurements into a model that can flag promising compounds in libraries nobody
has screened.
""".strip()

# --- Page text ---------------------------------------------------------------
# Heading and standfirst for each page, keyed by its function in steps.py.
STEP_TEXT = {
    "understand_the_data": (
        "*Staphylococcus aureus* activity in EU-OPENSCREEN",
        "We have downloaded the available data from the ECBD related to the *S. aureus* "
        "screening from EU-OPENSCREEN. Read their information to understand what we are "
        "looking at.",
    ),
    "choose_a_cutoff": ("Where does active begin?", ""),
    "train_a_model": (
        "Train supervised ML models using two molecular featurizers", ""
    ),
    "screen_a_library": ("Run a small virtual screening experiment", ""),
    "the_full_picture": ("The Ersilia Model Hub as a quick profiling tool", ""),
    "collective_picks": (
        "What did the room choose?",
        "Let's discuss collections from colleagues.",
    ),
    "hit_expansion": ("Can you beat the natural product?", ""),
}

# data/saureus.csv is a downsample. scripts/01_prepare_saureus_dataset.py kept
# every compound at or above DOWNSAMPLE_ABOVE and sampled the rest, which leaves
# a cliff in the histogram at that value. The two counts are what it kept below
# the line and what the source screen held, so their ratio undoes the sampling.
DOWNSAMPLE_ABOVE = 50
DOWNSAMPLE_KEPT = 9379
DOWNSAMPLE_SOURCE = 100247

# Shown on hover over the Inactives count, which is the number it qualifies.
SAMPLING_CAVEAT = (
    "Every active was kept while the inactives were downsampled to fit 10,000 rows, so "
    "this split is about ten times richer in actives than the real screen. The histogram "
    "corrects for that; these counts do not, and they are what the model trains on. A "
    "teaching set, not a basis for any claim about how often a screen hits."
)

# The form the room fills in on the Profiling step, and the sheet it publishes
# to. The sheet is read live, on demand - see steps.collective_picks.
# Set RAFIKI_RESPONSES_URL to point a later edition at its own sheet, or at a
# local .tsv to work on this page offline.
FORM_RESPONSES_URL = os.environ.get(
    "RAFIKI_RESPONSES_URL",
    "https://docs.google.com/spreadsheets/d/e/2PACX-1vQCwmm4HWb3xYvHfTXdYFBUsk57BQMDTD"
    "w0xKP1AqNWH3rG5x8BexDPMsEctT1Uav5kjeU-y974JvPk/pub"
    "?gid=478356490&single=true&output=tsv",
)
RESPONSE_NAME_COLUMN = "Your name"
# Structures per page on the Collective step.
N_COLLECTIVE_PAGE = 24
RESPONSE_CANDIDATE_COLUMNS = ["Candidate {0}".format(i) for i in range(1, 6)]

# Where the room submits its five candidates. The sheet above is what this
# form writes into, and the Collective step reads back.
PICKS_FORM_URL = "https://forms.gle/RFuF4bn3bFZudM5G9"
# The last thing in the workshop.
CLOSING_TITLE = "That is the whole loop"
CLOSING = (
    "You started from a plate of measurements and decided what counts as active. You "
    "trained two models on two different ways of describing a molecule, and let one of "
    "them rank a thousand compounds nobody in the room had screened. You looked past "
    "activity at everything else that can stop a compound, and then asked a generative "
    "model for better versions of a hit. That is a drug discovery cycle, in miniature - "
    "and every model you used is free, open, and in the Ersilia Model Hub."
)

MODEL_HUB_URL = "https://ersilia.io/model-hub"

# Every Ersilia model behind a number in this app. Titles are the models' own.
MODELS = {
    "eos1klk": "2D projector trained on the Ersilia reference library",
    "eos4wt0": "Morgan fingerprints, binary, radius 3, 2048 bits",
    "eos9o72": "CheMeleon embeddings",
    "eos8lcw": "Antimicrobial activity against S. aureus, from ChEMBL and PubChem",
    "eos42ez": "Human cytotoxicity endpoints",
    "eos7m30": "ADMET properties prediction (hERG endpoint)",
    "eos9ei3": "Synthetic accessibility score",
    "eos9yui": "Natural product likeness score",
    "eos2xeq": "Antibiotic downselection, similarity to known antibiotics",
    "eos4djh": "Basic molecular descriptors from Datamol",
    "eos3lyd": "Efflux pump avoidance in gram-negative bacteria",
    "eos5eya": "Antimicrobial activity against E. coli, from ChEMBL and PubChem",
    "eos6wb7": "Antimicrobial activity against K. pneumoniae, from ChEMBL and PubChem",
    "eos4q1a": "CReM fragment based structure generation",
    "eos6ost": "REINVENT 4 LibInvent",
    "eos84nf": "GenMol scaffold decoration",
    "eos694w": "REINVENT 4 Mol2Mol medium similarity",
    "eos57bx": "REINVENT 4 Mol2Mol scaffold",
}

# Which of them produced the numbers on each page.
STEP_MODELS = {
    "understand_the_data": ["eos1klk"],
    "train_a_model": ["eos4wt0", "eos9o72"],
    "screen_a_library": ["eos8lcw"],
    "the_full_picture": ["eos8lcw", "eos42ez", "eos7m30", "eos9ei3", "eos9yui",
                         "eos2xeq", "eos4djh"],
    "hit_expansion": ["eos4q1a", "eos6ost", "eos8lcw", "eos3lyd", "eos5eya", "eos6wb7"],
}

PROFILING_INTRO = (
    "Explore the table carefully and try to understand the meaning of the columns and "
    "their dimensions. Not all columns are equally important. These columns come from "
    "the [Ersilia Model Hub](https://catalog.ersilia.io). You can find the corresponding "
    "publications in [this folder](https://drive.google.com/drive/folders/"
    "1fk-nfM5hU2O5MwufJNSCBEfypi-nGqD6?usp=sharing)."
)

# The green note on the same page. This is a natural products course.
NATURAL_PRODUCTS_NOTE = (
    "This is a natural products course, so it would be good to prioritise natural "
    "products. Natural product likeness is the column for that - the higher the "
    "score, the more the compound looks like something nature would make."
)

# How many of the table's rows to draw as structures underneath it.
N_PROFILE_SHOWN = 16

ECBD_ASSAY_URL = "https://ecbd.eu/assays/EOS300078"

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
# CUTOFF_DEFAULT = None starts the slider at the mean of the readout.
# The step matches the pretrained grid: one entry per whole percent, so every
# position the slider can reach has been trained. See scripts/06_pretrain_models.py.
CUTOFF_MIN, CUTOFF_MAX, CUTOFF_STEP = 0.0, 100.0, 1.0
CUTOFF_DEFAULT = None

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

# Cross-validation results for every descriptor at every whole-percent cut-off,
# built by scripts/06_pretrain_models.py. The Train page reads this and fits
# nothing; the descriptor matrices are never loaded by the app.
PRETRAINED_FILE = "pretrained.npz"

# Revealed a line at a time when a model is opened. Each is a true statement
# about how the numbers were produced.
TRAINING_STEPS = [
    "{descriptor}: {n_features} numbers per molecule",
    "Random forest, {n_trees} trees",
    "{n_splits}-fold stratified split, {test_pct}% held out each time",
    "AUROC averaged over the {n_splits} held-out folds",
]
TRAINING_SECONDS = 5.0
PROJECTION_X, PROJECTION_Y = "tsne_x", "tsne_y"

# --- Screening libraries -----------------------------------------------------
# Each group is handed a SMILES file matching one of these. Predictions are
# already computed; the app matches the upload to a library by SMILES overlap.
LIBRARY_FILES = [
    "library_1.csv", "library_2.csv", "library_3.csv",
    "library_4.csv", "library_5.csv", "library_6.csv",
]
LIBRARY_SMILES_COLUMN = "input"

# Stable identifiers for every compound across the six libraries, assigned once
# by scripts/04_assign_rafiki_ids.py and committed. Not generated at runtime:
# a participant's RAFIKI-0421 has to mean the same compound in every session.
RAFIKI_IDS_FILE = "rafiki_ids.csv"
RAFIKI_ID_LABEL = "RAFIKI ID"

# Column headings as a reader should see them. "smiles" and "growth_inhibition"
# are the names in the CSVs; these are what the tables show. Renamed at display
# time only - "smiles" stays the join key everywhere in the code.
SMILES_LABEL = "SMILES"
READOUT_TABLE_LABEL = "Growth Inhibition"

# One colour per library, from the house categorical set, so each group can be
# pointed at "the green one" from the front of the room.
LIBRARY_COLOURS = ["#6d5de7", "#e2a72e", "#247dad", "#6cbf5a", "#af5cc7", "#e63745"]


# The two S. aureus activity predictions shown first.
# One bioactivity model, to keep the screening step short. eos3f8h is the other
# S. aureus model in these files; it saturates (almost everything scores above
# 0.99), so ChEMBL is the one worth showing.
ACTIVITY_MODEL_LABEL = "S. aureus bioactivity"
ACTIVITY_MODEL_COLUMN = "eos8lcw_consensus_score"

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

N_TOP_HITS = 24        # shown as structures once the screen has run

# --- Hit expansion -----------------------------------------------------------
# One natural product, platensimycin, sits in all six libraries and ranks in the
# top 1.5% on the ChEMBL model, so every group finds it. These are 1062 analogues
# from five generative models, already scored.
ANALOGUES_FILE = "analogues_master.csv"
PARENT_NAME = "Platensimycin"

# The real, stereo-defined natural product: the input the generators were given.
# The copy inside the libraries is flat, which is why it scores 0.825 not 0.830.
PARENT_SMILES = (
    "C[C@]12C[C@]34C[C@H]1C[C@@H]([C@H]3[C@](C(=O)C=C4)(C)CCC(=O)"
    "NC5=C(C=CC(=C5O)C(=O)O)O)O2"
)

# Only these two generators are shown. CReM is the one that keeps the
# stereochemistry and the parent's size; LibInvent shows what a scaffold
# decorator does. GenMol and mol2mol are in the file but out of the workshop.
ANALOGUE_GENERATORS = ["CReM", "LibInvent"]

GENERATORS = [
    {
        "name": "CReM",
        "model": "eos4q1a",
        "input_label": "Input: the whole molecule",
        "input_smiles": PARENT_SMILES,
        "text": "Swaps small fragments for alternatives seen in real molecules, leaving "
                "the rest untouched. The only generator here that keeps all six "
                "stereocentres and stays near the parent's weight.",
    },
    {
        "name": "LibInvent",
        "model": "eos6ost",
        "input_label": "Input: a scaffold with one attachment point",
        "input_smiles": (
            "C[C@]12C[C@@]34C=CC(=O)[C@@](C)(CCC(=O)Nc5c(O)c([*])cc(C(=O)O)c5O)"
            "[C@@H]3[C@H](C[C@@H]1C4)O2"
        ),
        "text": "Grows substituents at the position marked [*] and freezes everything "
                "else. Run on the bare molecule instead, it strips the benzoic-acid head "
                "- and the activity goes with it.",
    },
]

# Reference values for the stereo-defined natural product.
PARENT_SAUREUS, PARENT_EFFLUX = 0.830, 0.492
SAUREUS_THRESHOLD = 0.791

PARENT_BLURB = (
    "Platensimycin is a known FabF inhibitor of natural origin, active against "
    "Gram-positives but effluxed in Gram-negatives. It was identified by Merck "
    "([Wang et al., *Nature*, 2006](https://www.nature.com/articles/nature04784))."
)

EFFLUX_BLURB = (
    "A Gram-negative cell pumps most small molecules straight back out. "
    "`eos3lyd` was trained on Co-ADD data for 73,000 compounds screened against "
    "wild-type *E. coli* alongside efflux-deficient and hyperpermeable strains: "
    "comparing the strains says whether a compound was kept out or pumped out. "
    "The model returns the probability that a molecule **evades** efflux, so higher "
    "is better. Platensimycin scores {0}."
)

# Gram-negative activity, with each model's own recommended threshold.
GRAM_NEGATIVE = [
    ("E. coli", "ch_ecoli", 0.855, 0.636, "eos5eya"),
    ("K. pneumoniae", "ch_kpneumoniae", 0.837, 0.611, "eos6wb7"),
]

N_GENERATOR_EXAMPLES = 10

ANALOGUE_X, ANALOGUE_Y = "ch_saureus", "efflux_evader_proba"
ANALOGUE_SHORTLIST = "on_pareto_shortlist"

# --- Discussion questions ----------------------------------------------------
q1 = [
    "- What does each row represent?",
    "- What exactly was measured, and in what units?",
    "- Do we want higher or lower values?",
]

q2 = [
    "- Why do we need a cut-off at all?",
    "- What do 0 and 1 mean once we binarise?",
    "- Is this dataset balanced?",
]

q3 = [
    "- What does a Morgan fingerprint encode? And a learned embedding?",
    "- What is a cross-validation experiment, and why do we need one?",
    "- Which descriptor performs better? Is the difference meaningful?",
    "- Would a different cut-off change the ranking?",
]

# How many compounds to show before any score is revealed, and how long the
# prediction run takes to play out.
N_SCREEN_PREVIEW = 24
SCREENING_SECONDS = 2.0

q4 = [
    "- What does the activity score mean?",
    "- Which would be a good score cutoff?",
    "- What else would help us make a decision of which molecules to test?",
]

q5 = [
    "- Activity is not enough. What else in this table matters?",
    "- Would you pick compounds that resemble known antibiotics?",
    "- You can synthesise 5 compounds, which ones and why?",
]

q7 = [
    "- There is a known natural product antibiotic in the libraries. Did we find it?",
]

q6 = [
    "- CReM and LibInvent were given different inputs. Look at what that did.",
    "- Was this a real scaffold hopping exercise?",
    "- The diamond is platensimycin. Which quadrant do you want to be in?",
    "- Analogues that gain permeability without losing potency: would you make them?",
    "- Nothing here clears the E. coli threshold. What is that telling you?",
]
