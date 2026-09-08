"""Train the workshop's models once, for every cut-off, and store what the app shows.

The Train page used to fit six random forests over a 10,000 x 2048 matrix per
descriptor while a participant waited - about 5s and 10s on a developer laptop,
considerably worse on a shared container with a room full of people pressing the
button at the same moment. Nothing about that work is per-participant: the only
thing a participant chooses is the cut-off, and there are 101 of those.

So the grid is built here, once. The page reads it and fits nothing.

Outputs
    data/pretrained.npz     the grid the app reads. Small, committed.
    data/models/*.joblib    the fitted forests, one per descriptor and cut-off.
    data/pretrained_parts/  one file per cell, so a killed run can resume.

The models are ~7 MB each compressed, so the full set is about 1.4 GB. They are
NOT committed - .gitignore keeps data/models/ and data/pretrained_parts/ out -
but they are kept on disk, because a trained model is worth having even though
this app does not use one. The app scores libraries from columns already in the
CSVs; nothing here is loaded at runtime except pretrained.npz.

Resuming
    Every cell is written atomically and skipped if it is already there, so
    re-running after a crash, a laptop closing or a Ctrl-C picks up where it
    stopped. Delete a part file to force that cell to be redone.

What is stored is exactly what the page draws: the five fold AUROCs, the
interpolated ROC curves, and one fold's held-out scores. X is not stored - at
82 MB per descriptor it was the largest thing in a session.

The split is seeded, so the grid is reproducible and the cut-offs are comparable
to each other: the same split at every cut-off, only the labels move. The code
this replaces left train_test_split unseeded, so the same click gave different
AUROCs each time.

Roughly 30 minutes for the full grid with models, 20 without (--no-models).
"""

import argparse
import json
import os
import sys
import time

import joblib
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(root, "..", "app"))

from info import (                                                  # noqa: E402
    CUTOFF_MAX, CUTOFF_MIN, DESCRIPTORS, HIGHER_IS_ACTIVE, TRAINING_FILE,
)
from utils import (                                                 # noqa: E402
    binarize, data_path, descriptor_preview, interpolate_roc_curves,
    load_descriptors, load_training_data,
)

RANDOM_SEED = 42
N_SPLITS = 5
N_TREES = 100
TEST_SIZE = 0.2
N_ROC_POINTS = 100
MODEL_COMPRESSION = 3          # 39 MB -> 7 MB, and still loads with joblib.load

OUTPUT = "pretrained.npz"
PARTS_DIR = "pretrained_parts"
MODELS_DIR = "models"


def slug(label):
    return label.lower().replace(" ", "_")


def cell_name(label, cutoff):
    return "{0}__{1:05.1f}".format(slug(label), cutoff)


def write_atomic(path, write):
    """Write via a temporary file and rename, so a kill cannot leave a half
    written part that a later run would trust and skip.

    `write` is handed an open file rather than a path: np.savez_compressed
    appends ".npz" to a path that lacks it, which would rename the wrong file.
    """
    tmp = path + ".partial"
    with open(tmp, "wb") as handle:
        write(handle)
    os.replace(tmp, path)


def cross_validate(X, y):
    """Five stratified 80/20 fits: the AUROCs and each fold's held-out labels
    and scores, which is all the page ever draws."""
    aurocs, folds = [], []
    for split in range(N_SPLITS):
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=TEST_SIZE, stratify=y,
            random_state=RANDOM_SEED + split,          # same split at every cut-off
        )
        model = RandomForestClassifier(n_estimators=N_TREES, n_jobs=-1,
                                       random_state=RANDOM_SEED)
        model.fit(X_train, y_train)
        aurocs.append(roc_auc_score(y_test, model.predict_proba(X_test)[:, 1]))
        folds.append((y_test, model.predict_proba(X_test)[:, 1]))
    return aurocs, folds


def build_cell(X, y, label, cutoff, parts, models, keep_models):
    """One descriptor at one cut-off. Returns the arrays the grid needs."""
    part_path = os.path.join(parts, cell_name(label, cutoff) + ".npz")
    model_path = os.path.join(models, cell_name(label, cutoff) + ".joblib")
    wanted = (not keep_models) or os.path.exists(model_path)
    if os.path.exists(part_path) and wanted:
        with np.load(part_path) as cell:
            return {k: cell[k] for k in cell.files}, True

    aurocs, folds = cross_validate(X, y)
    curves = interpolate_roc_curves(folds, n_points=N_ROC_POINTS)
    cell = {
        "aurocs": np.array(aurocs, dtype=np.float32),
        "roc_tpr": np.stack([curves["tpr_cv{0}".format(f + 1)].to_numpy()
                             for f in range(N_SPLITS)]).astype(np.float32),
        "roc_mean": curves["Mean TPR"].to_numpy().astype(np.float32),
        "fold_y": folds[0][0].astype(np.uint8),
        "fold_p": folds[0][1].astype(np.float32),
    }
    write_atomic(part_path, lambda h: np.savez_compressed(h, **cell))

    if keep_models and not os.path.exists(model_path):
        # Fitted on every row, unlike the cross-validation folds: this is the
        # one worth keeping, and the app never loads it.
        whole = RandomForestClassifier(n_estimators=N_TREES, n_jobs=-1,
                                       random_state=RANDOM_SEED).fit(X, y)
        write_atomic(model_path,
                     lambda h: joblib.dump(whole, h, compress=MODEL_COMPRESSION))
    return cell, False


def main(cutoffs, keep_models):
    parts = data_path(PARTS_DIR)
    models = data_path(MODELS_DIR)
    for d in (parts, models):
        os.makedirs(d, exist_ok=True)

    df = load_training_data(TRAINING_FILE)
    labels = list(DESCRIPTORS)
    n_d, n_c = len(labels), len(cutoffs)

    aurocs = np.zeros((n_d, n_c, N_SPLITS), dtype=np.float32)
    roc_tpr = np.zeros((n_d, n_c, N_SPLITS, N_ROC_POINTS), dtype=np.float32)
    roc_mean = np.zeros((n_d, n_c, N_ROC_POINTS), dtype=np.float32)
    fold_y = fold_p = None
    meta = {"seed": RANDOM_SEED, "n_splits": N_SPLITS, "n_trees": N_TREES,
            "test_size": TEST_SIZE, "descriptors": labels,
            "cutoffs": [float(c) for c in cutoffs], "preview": {}, "shape": {}}

    for d, label in enumerate(labels):
        X = load_descriptors(DESCRIPTORS[label])
        meta["preview"][label] = descriptor_preview(X)
        meta["shape"][label] = list(X.shape)
        print("{0}: X={1}".format(label, X.shape), flush=True)
        for c, cutoff in enumerate(cutoffs):
            started = time.time()
            y = np.array(binarize(df, cutoff, HIGHER_IS_ACTIVE)["Binary"])
            cell, resumed = build_cell(X, y, label, cutoff, parts, models, keep_models)

            aurocs[d, c] = cell["aurocs"]
            roc_tpr[d, c] = cell["roc_tpr"]
            roc_mean[d, c] = cell["roc_mean"]
            if fold_y is None:
                n_test = len(cell["fold_y"])
                fold_y = np.zeros((n_d, n_c, n_test), dtype=np.uint8)
                fold_p = np.zeros((n_d, n_c, n_test), dtype=np.float32)
            fold_y[d, c] = cell["fold_y"]
            fold_p[d, c] = cell["fold_p"]

            print("  {0:5.1f}  AUROC {1:.3f} +/- {2:.3f}  {3}".format(
                cutoff, float(np.mean(cell["aurocs"])), float(np.std(cell["aurocs"])),
                "cached" if resumed else "{0:.1f}s".format(time.time() - started)),
                flush=True)
        del X

    target = data_path(OUTPUT)
    write_atomic(target, lambda h: np.savez_compressed(
        h, aurocs=aurocs, roc_fpr=np.linspace(0, 1, N_ROC_POINTS).astype(np.float32),
        roc_tpr=roc_tpr, roc_mean=roc_mean, fold_y=fold_y, fold_p=fold_p,
        cutoffs=np.array(cutoffs, dtype=np.float32), meta=np.array(json.dumps(meta))))
    print("wrote {0} ({1:.1f} MB)".format(
        os.path.relpath(target, root), os.path.getsize(target) / 1e6))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cutoffs", type=float, nargs="+",
                        help="only these cut-offs, for a quick check")
    parser.add_argument("--no-models", action="store_true",
                        help="skip the joblib forests (~1.4 GB) and only build the grid")
    args = parser.parse_args()
    grid = args.cutoffs or [float(c) for c in
                            range(int(CUTOFF_MIN), int(CUTOFF_MAX) + 1)]
    main(grid, keep_models=not args.no_models)
