import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root)

from info import (
    TITLE, PAGE_ICON, about, intro,
    TRAINING_FILE, SMILES_COLUMN, READOUT_COLUMN, READOUT_LABEL, HIGHER_IS_ACTIVE,
    CUTOFF_MIN, CUTOFF_MAX, CUTOFF_DEFAULT, CUTOFF_STEP,
    DESCRIPTORS, PROJECTION_FILE, PROJECTION_X, PROJECTION_Y,
    LIBRARY_FILES, LIBRARY_SMILES_COLUMN, ACTIVITY_MODELS, COLUMN_LABELS, N_TOP_HITS,
    EXAMPLE_INPUT,
    q1, q2, q3, q4, q5,
)
from utils import (
    data_path, descriptor_preview, load_training_data, binarize, load_descriptors,
    load_projection, load_library, read_uploaded_smiles, match_library,
    reduce_dimensions, train_classifier, interpolate_roc_curves, draw_molecules_grid,
)
from plots import (
    plot_readout_histogram, plot_chemical_space, plot_roc, plot_model_agreement,
)

st.set_page_config(layout="wide", page_title=TITLE, page_icon=PAGE_ICON, initial_sidebar_state="collapsed")

def data_version(filename):
    """Part of every cache key, so a regenerated file is never served stale."""
    return os.path.getmtime(data_path(filename))


@st.cache_data(show_spinner=False)
def _training_data(filename, version):
    return load_training_data(filename)


@st.cache_data(show_spinner=False)
def _descriptors(filename, version):
    return load_descriptors(filename)


@st.cache_data(show_spinner=False)
def _library(filename, version):
    return load_library(filename)


@st.cache_data(show_spinner=False)
def _projection(filename, version):
    return load_projection(filename)


def cached_training_data(filename):
    return _training_data(filename, data_version(filename))


def cached_descriptors(filename):
    return _descriptors(filename, data_version(filename))


def cached_library(filename):
    return _library(filename, data_version(filename))


def cached_projection(filename):
    return _projection(filename, data_version(filename))


def unlocked(key, label):
    """Show a button once; remember for the rest of the session that it was clicked."""
    if not st.session_state.get(key):
        st.session_state[key] = st.button(label, key="button_" + key)
    return st.session_state[key]


def questions(container, items):
    container.info("  \n".join(items), icon=":material/quiz:")


st.session_state.setdefault("features", {})
st.session_state.setdefault("models", {})
st.session_state.setdefault("predictions", {})

st.sidebar.title("About")
for line in about:
    st.sidebar.write(line)
st.sidebar.image(
    os.path.join(root, "..", "assets", "ersilia_brand.png"),
    width="stretch",
    caption="Designed with ❤️ by the Ersilia Open Source Initiative",
)

st.title("{0} {1}".format(PAGE_ICON, TITLE))
st.info(intro)

if os.path.exists(data_path(".placeholder")):
    st.error(
        "Descriptors and projection are RANDOM PLACEHOLDER data, not real model output. "
        "See scripts/99_placeholder_descriptors.py.",
        icon=":material/warning:",
    )

if not os.path.exists(data_path(TRAINING_FILE)):
    st.error(
        "Missing training data. Place `{0}` in `data/`, with at least the columns "
        "`{1}` and `{2}`. File names are configured in `app/info.py`.".format(
            TRAINING_FILE, SMILES_COLUMN, READOUT_COLUMN
        )
    )
    st.stop()

# Step 1 -----------------------------------------------------------------------
st.header("Step 1: Understand your data")
df = cached_training_data(TRAINING_FILE)
cols = st.columns([2, 1])
cols[0].write(df[[SMILES_COLUMN, READOUT_COLUMN]])
questions(cols[1], q1)

if unlocked("step1", "Move to the next section"):

    # Step 2 -------------------------------------------------------------------
    st.divider()
    st.header("Step 2: Choose an activity cut-off")

    cols = st.columns(5)
    cols[0].metric("Mean {0}".format(READOUT_LABEL.lower()), round(df[READOUT_COLUMN].mean(), 2))
    cols[1].metric("Standard deviation", round(df[READOUT_COLUMN].std(), 2))
    cutoff = cols[2].slider(
        "Activity cut-off", CUTOFF_MIN, CUTOFF_MAX, CUTOFF_DEFAULT, CUTOFF_STEP, format="%.1f"
    )
    dt = binarize(df, cutoff, HIGHER_IS_ACTIVE)
    cols[3].metric("Actives", int(dt["Binary"].sum()))
    cols[4].metric("Inactives", int(len(dt) - dt["Binary"].sum()))

    cols = st.columns(2)
    cols[0].altair_chart(
        plot_readout_histogram(dt, READOUT_COLUMN, cutoff, READOUT_LABEL), width="stretch"
    )
    if os.path.exists(data_path(PROJECTION_FILE)):
        cols[1].altair_chart(
            plot_chemical_space(
                cached_projection(PROJECTION_FILE), PROJECTION_X, PROJECTION_Y, dt["Binary"]
            ),
            width="stretch",
        )
    else:
        cols[1].warning("Missing `data/{0}`.".format(PROJECTION_FILE))
    questions(st, q2)

    if st.button("Cut-off selected"):
        if st.session_state.get("cutoff") != cutoff:
            # Anything fitted against the old labels is now stale.
            for key in ("features", "models", "predictions"):
                st.session_state[key].clear()
        st.session_state["cutoff"] = cutoff

if st.session_state.get("cutoff") is not None:
    y = list(binarize(df, st.session_state["cutoff"], HIGHER_IS_ACTIVE)["Binary"])
    st.success("Cut-off in use: {0}".format(st.session_state["cutoff"]))

    # Step 3 -------------------------------------------------------------------
    st.divider()
    st.header("Step 3: Train a model")

    cols = st.columns(len(DESCRIPTORS))
    for i, (label, filename) in enumerate(DESCRIPTORS.items()):
        col = cols[i]
        if col.button("🤖 Train a model with {0}".format(label), key="train_" + label):
            if not os.path.exists(data_path(filename)):
                col.warning("Missing `data/{0}`.".format(filename))
            else:
                with st.spinner("Calculating {0} and training...".format(label)):
                    X = cached_descriptors(filename)
                    reducer, X_reduced = reduce_dimensions(X, y)
                    st.session_state["features"][label] = {
                        "reducer": reducer, "X": X_reduced, "preview": descriptor_preview(X),
                        "shape": X.shape,
                    }
                    st.session_state["models"][label] = train_classifier(X_reduced, y)
        if label in st.session_state["models"]:
            feature = st.session_state["features"][label]
            col.caption("One molecule as {0} ({1} features):".format(label.lower(), feature["shape"][1]))
            col.code(feature["preview"], language=None)
            aurocs = st.session_state["models"][label]["aurocs"]
            col.metric("AUROC ± Std", "{0:.3f} ± {1:.3f}".format(np.mean(aurocs), np.std(aurocs)))
            col.altair_chart(
                plot_roc(interpolate_roc_curves(st.session_state["models"][label]["cv_data"])),
                width="stretch",
            )

    questions(st, q3)

    # Step 4 -------------------------------------------------------------------
    st.divider()
    st.header("Step 4: Screen a new library")

    cols = st.columns([0.7, 0.3])
    uploaded = cols[0].file_uploader(
        "Drop the SMILES file your group was given", type=["csv", "smi", "txt"]
    )
    if os.path.exists(data_path(EXAMPLE_INPUT)):
        with open(data_path(EXAMPLE_INPUT), "rb") as f:
            cols[1].download_button("No file? Download an example", f, file_name="example_input.csv")
    if uploaded is not None:
        smiles_list = read_uploaded_smiles(uploaded)
        filename, n_matched = match_library(smiles_list, LIBRARY_FILES, LIBRARY_SMILES_COLUMN)
        if filename is None:
            st.error("None of the prepared libraries match this file. Check you uploaded the right one.")
        else:
            st.session_state["library"] = filename
            st.success(
                "Matched **{0}** - {1} of your {2} compounds found.".format(
                    filename, n_matched, len(smiles_list)
                )
            )

    if st.session_state.get("library"):
        library = cached_library(st.session_state["library"])
        primary_label, primary_column = list(ACTIVITY_MODELS.items())[0]
        second_label, second_column = list(ACTIVITY_MODELS.items())[1]
        ranked = library.sort_values(primary_column, ascending=False)

        cols = st.columns([0.45, 0.55])
        cols[0].altair_chart(
            plot_model_agreement(library, second_column, primary_column, second_label, primary_label),
            width="stretch",
        )
        cols[1].caption("Top {0} compounds by {1}".format(N_TOP_HITS, primary_label.lower()))
        top = ranked.head(N_TOP_HITS)
        legends = [
            "{0:.2f} / {1:.2f}".format(a, b)
            for a, b in zip(top[primary_column], top[second_column])
        ]
        cols[1].image(
            draw_molecules_grid(list(top[LIBRARY_SMILES_COLUMN]), legends),
            caption="Captions: {0} / {1}".format(primary_label.lower(), second_label.lower()),
        )
        questions(st, q4)

        # Step 5 ---------------------------------------------------------------
        st.divider()
        st.header("Step 5: The full picture")

        table = ranked.rename(columns={
            LIBRARY_SMILES_COLUMN: "smiles",
            primary_column: primary_label,
            second_column: second_label,
            **COLUMN_LABELS,
        })
        table = table[["smiles", primary_label, second_label] + list(COLUMN_LABELS.values())]
        st.dataframe(table, height=420)
        st.download_button(
            "Download this table",
            table.to_csv(index=False).encode(),
            file_name=st.session_state["library"].replace(".csv", "_predictions.csv"),
            mime="text/csv",
        )
        questions(st, q5)
