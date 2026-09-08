import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

from info import (
    DOWNSAMPLE_ABOVE, DOWNSAMPLE_KEPT, DOWNSAMPLE_SOURCE, READOUT_COLUMN,
)

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))


def data_path(filename):
    return os.path.join(DATA_DIR, filename)


def load_training_data(filename):
    df = pd.read_csv(data_path(filename))
    df[READOUT_COLUMN] = pd.to_numeric(df[READOUT_COLUMN])
    return df


def binarize(df, cutoff, higher_is_active):
    df = df.copy()
    values = df[READOUT_COLUMN]
    df["Binary"] = (values >= cutoff if higher_is_active else values <= cutoff).astype(int)
    return df


def screen_scale(df, readout_column):
    """Add a per-compound weight that undoes the downsampling, for display only.

    Compounds at or above DOWNSAMPLE_ABOVE were all kept, so they stand for
    themselves and weigh 1. Those below it survived at DOWNSAMPLE_KEPT of
    DOWNSAMPLE_SOURCE, so each one stands for that many times more. Summing the
    weights over a histogram bin estimates what the original screen held there,
    which is what makes the cliff at the sampling threshold disappear.

    Nothing that is fitted or counted elsewhere uses this: the model trains on
    the rows as they are.
    """
    df = df.copy()
    df["Weight"] = np.where(
        df[readout_column] >= DOWNSAMPLE_ABOVE, 1.0, DOWNSAMPLE_SOURCE / DOWNSAMPLE_KEPT
    )
    return df


def load_descriptors(filename):
    """Descriptor matrix, rows aligned with the training set."""
    return np.load(data_path(filename))["features"].astype(np.float32, copy=False)


def load_projection(filename):
    return pd.read_csv(data_path(filename))


def descriptor_preview(X, n_values=20):
    """First few values of one molecule, as the student would see them."""
    row = X[0][:n_values]
    if np.array_equal(row, row.astype(int)):
        return "  ".join(str(int(v)) for v in row) + "  ..."
    return "  ".join("{0:.3f}".format(v) for v in row) + "  ..."


def load_library(filename):
    return pd.read_csv(data_path(filename))


def load_rafiki_ids(filename):
    return pd.read_csv(data_path(filename))


def load_responses(url):
    """The published form responses, read live from Google Sheets.

    Returned with the moment it was fetched, because the sheet changes while the
    workshop is running and a stale table with no timestamp is worse than none.
    """
    return pd.read_csv(url, sep="\t"), datetime.now(timezone.utc)


def normalise_rafiki_id(text):
    """Read a hand-typed identifier as RAFIKI-0000, or None if it is not one.

    Participants type these into a form, so accept what they plausibly write:
    lower case, missing prefix, missing zero padding, stray whitespace.
    """
    if text is None:
        return None
    match = re.fullmatch(r"(?:RAFIKI[\s_-]*)?0*(\d{1,4})", str(text).strip().upper())
    return "RAFIKI-{0:04d}".format(int(match.group(1))) if match else None


def load_catalogue(library_filenames, smiles_column, activity_column):
    """Every library in one frame, for looking a compound up without knowing
    which group had it."""
    frames = [pd.read_csv(data_path(f))[[smiles_column, activity_column]]
              for f in library_filenames]
    catalogue = pd.concat(frames, ignore_index=True)
    return catalogue.drop_duplicates(subset=[smiles_column])


def load_analogues(filename):
    return pd.read_csv(data_path(filename))


def train_classifier(X, y, n_splits=5, test_size=0.2):
    X, y = np.array(X), np.array(y)
    model = RandomForestClassifier(n_jobs=-1)
    aurocs, cv_data = [], []
    for _ in range(n_splits):
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, stratify=y)
        model.fit(X_train, y_train)
        y_pred = model.predict_proba(X_test)[:, 1]
        aurocs += [roc_auc_score(y_test, y_pred)]
        cv_data += [(y_test, y_pred)]
    model.fit(X, y)
    return {"model": model, "aurocs": aurocs, "cv_data": cv_data, "X": X, "y": y}


def interpolate_roc_curves(cv_data, n_points=100):
    """One row per FPR grid point, one column per CV fold, plus the mean TPR."""
    mean_fpr = np.linspace(0, 1, n_points)
    tprs = []
    for y_test, y_pred in cv_data:
        fpr, tpr, _ = roc_curve(y_test, y_pred)
        interp_tpr = np.interp(mean_fpr, fpr, tpr)
        interp_tpr[0] = 0.0
        tprs += [interp_tpr]
    mean_tpr = np.mean(tprs, axis=0)
    mean_tpr[-1] = 1.0
    df = pd.DataFrame({"tpr_cv{0}".format(i + 1): t for i, t in enumerate(tprs)})
    df["Mean TPR"] = mean_tpr
    df["FPR"] = mean_fpr
    return df
