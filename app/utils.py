import os

import numpy as np
import pandas as pd
from lol import LOL
from rdkit import Chem
from rdkit.Chem import Draw
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.model_selection import train_test_split

from info import READOUT_COLUMN

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


def load_analogues(filename):
    return pd.read_csv(data_path(filename))


def reduce_dimensions(X, y, n_components=100):
    n_components = min(n_components, X.shape[1])
    reducer = LOL(n_components=n_components)
    return reducer, reducer.fit_transform(X, np.array(y))


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


def draw_molecule(smiles, size=(200, 200)):
    """Draw a molecule. Any attachment point is picked out, since a bare `*` is
    easy to miss and it is the whole point of a scaffold."""
    mol = Chem.MolFromSmiles(smiles)
    dummies = [a.GetIdx() for a in mol.GetAtoms() if a.GetAtomicNum() == 0]
    if not dummies:
        return Draw.MolToImage(mol, size=size)
    return Draw.MolToImage(
        mol, size=size, highlightAtoms=dummies,
        highlightColor=(0.902, 0.216, 0.271),      # #e63745
    )


def draw_molecules_grid(smiles_list, legends, per_row=4, size=(260, 220)):
    mols = [Chem.MolFromSmiles(s) for s in smiles_list]
    return Draw.MolsToGridImage(mols, molsPerRow=per_row, subImgSize=size, legends=legends)
