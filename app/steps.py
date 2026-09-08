"""One function per step. Each is registered as a page in app.py."""

import os

import numpy as np
import pandas as pd
import streamlit as st

from cache import (
    cached_analogues, cached_descriptors, cached_library, cached_projection,
    cached_training_data,
)
from info import (
    ACTIVITY_MODELS, ANALOGUES_FILE, ANALOGUE_SHORTLIST, ANALOGUE_X, ANALOGUE_Y,
    COLUMN_LABELS, CUTOFF_DEFAULT, CUTOFF_MAX, CUTOFF_MIN, CUTOFF_STEP, DESCRIPTORS,
    EXAMPLE_INPUT, HIGHER_IS_ACTIVE, LIBRARY_FILES, LIBRARY_SMILES_COLUMN, N_TOP_HITS,
    PARENT_EFFLUX, PARENT_NAME, PARENT_SAUREUS, PARENT_SMILES, PROJECTION_FILE,
    PROJECTION_X, PROJECTION_Y, READOUT_COLUMN, READOUT_LABEL, SAUREUS_THRESHOLD,
    SMILES_COLUMN, TRAINING_FILE, q1, q2, q3, q4, q5, q6,
)
from plots import (
    plot_chemical_space, plot_model_agreement, plot_pareto, plot_readout_histogram, plot_roc,
)
from utils import (
    binarize, data_path, descriptor_preview, draw_molecule, draw_molecules_grid,
    interpolate_roc_curves, match_library, read_uploaded_smiles, reduce_dimensions,
    train_classifier,
)


def questions(items):
    """Discussion prompts: quiet, bordered, always readable."""
    with st.container(border=True):
        st.caption("Talk it through")
        st.markdown("\n".join(items))


def advance(key, label, icon=":material/arrow_forward:"):
    """Unlock the next page. Remembered for the rest of the session once clicked."""
    if not st.session_state.get(key):
        st.session_state[key] = st.button(label, key="button_" + key, icon=icon, type="primary")
    return st.session_state[key]


def labels():
    """The two activity models, in ranking order."""
    return list(ACTIVITY_MODELS.items())


def training_data():
    return cached_training_data(TRAINING_FILE)


def binary_labels():
    return list(binarize(training_data(), st.session_state["cutoff"], HIGHER_IS_ACTIVE)["Binary"])


# --- Step 1 ------------------------------------------------------------------

def understand_the_data():
    df = training_data()
    st.subheader("What your collaborators handed you")
    cols = st.columns([2, 1], gap="medium")
    cols[0].dataframe(df[[SMILES_COLUMN, READOUT_COLUMN]], height=460)
    with cols[1]:
        questions(q1)
    advance("step1", "I have read the data")


# --- Step 2 ------------------------------------------------------------------

def choose_a_cutoff():
    df = training_data()
    st.subheader("Where does active begin?")

    with st.container(border=True):
        cols = st.columns(5, vertical_alignment="center")
        cols[0].metric("Mean", round(df[READOUT_COLUMN].mean(), 2))
        cols[1].metric("Std deviation", round(df[READOUT_COLUMN].std(), 2))
        cutoff = cols[2].slider(
            "Activity cut-off", CUTOFF_MIN, CUTOFF_MAX, CUTOFF_DEFAULT, CUTOFF_STEP, format="%.1f"
        )
        dt = binarize(df, cutoff, HIGHER_IS_ACTIVE)
        cols[3].metric("Actives", int(dt["Binary"].sum()))
        cols[4].metric("Inactives", int(len(dt) - dt["Binary"].sum()))

    cols = st.columns(2, gap="medium")
    cols[0].caption("Distribution of {0}".format(READOUT_LABEL.lower()))
    cols[0].altair_chart(
        plot_readout_histogram(dt, READOUT_COLUMN, cutoff, READOUT_LABEL), width="stretch"
    )
    cols[1].caption("The library in Ersilia's reference chemical space")
    if os.path.exists(data_path(PROJECTION_FILE)):
        cols[1].altair_chart(
            plot_chemical_space(
                cached_projection(PROJECTION_FILE), PROJECTION_X, PROJECTION_Y, dt["Binary"]
            ),
            width="stretch",
        )
    else:
        cols[1].warning("Missing `data/{0}`.".format(PROJECTION_FILE))

    questions(q2)

    if st.button("Use this cut-off", icon=":material/check:", type="primary"):
        if st.session_state.get("cutoff") != cutoff:
            # Anything fitted against the old labels is now stale.
            for key in ("features", "models", "predictions"):
                st.session_state[key].clear()
        st.session_state["cutoff"] = cutoff
        st.rerun()

    if st.session_state.get("cutoff") is not None:
        st.success("Cut-off in use: {0}".format(st.session_state["cutoff"]))


# --- Step 3 ------------------------------------------------------------------

def train_a_model():
    if st.session_state.get("cutoff") is None:
        st.info("Choose a cut-off first.", icon=":material/info:")
        return

    y = binary_labels()
    st.subheader("Two ways to describe a molecule")

    cols = st.columns(len(DESCRIPTORS), gap="medium")
    for i, (label, filename) in enumerate(DESCRIPTORS.items()):
        with cols[i].container(border=True):
            st.markdown("**{0}**".format(label))
            if st.button("Train a model", key="train_" + label, icon=":material/play_arrow:"):
                if not os.path.exists(data_path(filename)):
                    st.warning("Missing `data/{0}`.".format(filename))
                else:
                    with st.spinner("Calculating {0} and training...".format(label)):
                        X = cached_descriptors(filename)
                        reducer, X_reduced = reduce_dimensions(X, y)
                        st.session_state["features"][label] = {
                            "reducer": reducer, "X": X_reduced,
                            "preview": descriptor_preview(X), "shape": X.shape,
                        }
                        st.session_state["models"][label] = train_classifier(X_reduced, y)
            if label in st.session_state["models"]:
                feature = st.session_state["features"][label]
                st.caption("One molecule, as {0} numbers".format(feature["shape"][1]))
                st.code(feature["preview"], language=None)
                aurocs = st.session_state["models"][label]["aurocs"]
                st.metric("AUROC", "{0:.3f} ± {1:.3f}".format(np.mean(aurocs), np.std(aurocs)))
                st.altair_chart(
                    plot_roc(interpolate_roc_curves(st.session_state["models"][label]["cv_data"])),
                    width="stretch",
                )

    questions(q3)
    if st.session_state["models"]:
        advance("step3", "Take a model to a new library")


# --- Step 4 ------------------------------------------------------------------

def screen_a_library():
    st.subheader("A thousand compounds you have never seen")

    cols = st.columns([0.7, 0.3], vertical_alignment="bottom")
    uploaded = cols[0].file_uploader(
        "Drop the SMILES file your group was given", type=["csv", "smi", "txt"]
    )
    if os.path.exists(data_path(EXAMPLE_INPUT)):
        with open(data_path(EXAMPLE_INPUT), "rb") as handle:
            cols[1].download_button(
                "No file? Take an example", handle, file_name="example_input.csv",
                icon=":material/download:",
            )

    if uploaded is not None:
        smiles_list = read_uploaded_smiles(uploaded)
        filename, n_matched = match_library(smiles_list, LIBRARY_FILES, LIBRARY_SMILES_COLUMN)
        if filename is None:
            st.error("None of the prepared libraries match this file.")
        else:
            st.session_state["library"] = filename
            st.success("Matched **{0}** - {1} of your {2} compounds found.".format(
                filename, n_matched, len(smiles_list)))

    if not st.session_state.get("library"):
        return

    library = cached_library(st.session_state["library"])
    (primary_label, primary_column), (second_label, second_column) = labels()
    ranked = library.sort_values(primary_column, ascending=False)

    cols = st.columns([0.45, 0.55], gap="medium")
    cols[0].caption("{0} against {1}".format(second_label, primary_label.lower()))
    cols[0].altair_chart(
        plot_model_agreement(library, second_column, primary_column, second_label, primary_label),
        width="stretch",
    )
    top = ranked.head(N_TOP_HITS)
    cols[1].caption("Top {0} by {1} - captions are {2} / {3}".format(
        N_TOP_HITS, primary_label.lower(), primary_label.lower(), second_label.lower()))
    cols[1].image(draw_molecules_grid(
        list(top[LIBRARY_SMILES_COLUMN]),
        ["{0:.2f} / {1:.2f}".format(a, b) for a, b in zip(top[primary_column], top[second_column])],
    ))

    questions(q4)
    advance("step4", "See everything we know about them")


# --- Step 5 ------------------------------------------------------------------

def the_full_picture():
    if not st.session_state.get("library"):
        st.info("Upload your library first.", icon=":material/info:")
        return

    library = cached_library(st.session_state["library"])
    (primary_label, primary_column), (second_label, second_column) = labels()
    st.subheader("Activity is only the first column")

    table = library.sort_values(primary_column, ascending=False).rename(columns={
        LIBRARY_SMILES_COLUMN: "smiles",
        primary_column: primary_label,
        second_column: second_label,
        **COLUMN_LABELS,
    })
    table = table[["smiles", primary_label, second_label] + list(COLUMN_LABELS.values())]
    st.dataframe(table, height=430)
    st.download_button(
        "Download this table", table.to_csv(index=False).encode(),
        file_name=st.session_state["library"].replace(".csv", "_predictions.csv"),
        mime="text/csv", icon=":material/download:",
    )
    questions(q5)
    advance("step5", "Expand the natural product in your hits")


# --- Step 6 ------------------------------------------------------------------

def hit_expansion():
    st.subheader("Can you beat the natural product?")
    analogues = cached_analogues(ANALOGUES_FILE)

    cols = st.columns([0.3, 0.7], gap="medium")
    with cols[0].container(border=True):
        st.image(draw_molecule(PARENT_SMILES, size=(280, 240)))
        st.markdown("**{0}**".format(PARENT_NAME))
        st.metric("S. aureus activity", PARENT_SAUREUS)
        st.metric("Efflux evasion", PARENT_EFFLUX)
    cols[0].caption(
        "It sits in every group's library. Potent against Gram-positives, useless against "
        "Gram-negatives - not because it misses its target, but because it never gets inside."
    )
    cols[1].caption(
        "{0} analogues from five generative models. Up and to the right of the parent is better "
        "on both axes.".format(len(analogues))
    )
    cols[1].altair_chart(
        plot_pareto(analogues, ANALOGUE_X, ANALOGUE_Y, ANALOGUE_SHORTLIST,
                    PARENT_SAUREUS, PARENT_EFFLUX, SAUREUS_THRESHOLD),
        width="stretch",
    )

    with st.container(border=True):
        cols = st.columns(4)
        cols[0].metric("Analogues", len(analogues))
        cols[1].metric("Keep potency", int(analogues["clears_saureus_thr"].sum()))
        cols[2].metric("Gain permeability", int(analogues["better_efflux_than_parent"].sum()))
        cols[3].metric("Both", int(analogues[ANALOGUE_SHORTLIST].sum()))
    questions(q6)
