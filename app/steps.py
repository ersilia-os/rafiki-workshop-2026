"""One function per step. Each is registered as a page in app.py."""

import os

import numpy as np
import streamlit as st

from cache import (
    cached_analogues, cached_descriptors, cached_library, cached_projection,
    cached_training_data,
)
from info import (
    ACTIVITY_MODEL_COLUMN, ACTIVITY_MODEL_LABEL, ANALOGUES_FILE, ANALOGUE_GENERATORS,
    ANALOGUE_SHORTLIST, ANALOGUE_X, ANALOGUE_Y, EFFLUX_BLURB, GENERATORS,
    GRAM_NEGATIVE, N_GENERATOR_EXAMPLES, PARENT_BLURB,
    COLUMN_LABELS, CUTOFF_DEFAULT, CUTOFF_MAX, CUTOFF_MIN, CUTOFF_STEP, DESCRIPTORS,
    HIGHER_IS_ACTIVE, LIBRARY_FILES, LIBRARY_SMILES_COLUMN, N_TOP_HITS,
    PARENT_EFFLUX, PARENT_NAME, PARENT_SAUREUS, PARENT_SMILES, PROJECTION_FILE,
    PROJECTION_X, PROJECTION_Y, READOUT_COLUMN, READOUT_LABEL, SAUREUS_THRESHOLD,
    MODELS, MODEL_HUB_URL, RESULTS_HINT, SAMPLING_CAVEAT, SMILES_COLUMN, STEP_MODELS, STEP_TEXT,
    TRAINING_FILE, ECBD_ASSAY_URL,
    q1, q2, q3, q4, q5, q6,
)
from plots import (
    plot_chemical_space, plot_fold_scores, plot_pareto, plot_readout_histogram, plot_roc,
    plot_score_distribution,
)
from molecules import draw_molecule, draw_molecules_grid
from utils import (
    binarize, data_path, descriptor_preview, interpolate_roc_curves, screen_scale,
    train_classifier,
)


def heading(step):
    """Page heading and standfirst, both editable in info.py."""
    title, body = STEP_TEXT[step]
    st.header(title)
    if body:
        st.markdown(body)


def models_used(step):
    """Name the Ersilia models behind this page, and point at the catalogue."""
    listed = "  \n".join(
        "- [`{0}`](https://github.com/ersilia-os/{0}) - {1}".format(i, MODELS[i])
        for i in STEP_MODELS[step]
    )
    with st.expander("Models used on this page", icon=":material/deployed_code:"):
        st.markdown(listed)
        st.caption(
            "There are over 250 models like these, free to browse and run, in the "
            "[Ersilia Model Hub]({0}).".format(MODEL_HUB_URL)
        )


def hint(text):
    """Guidance on how to read a page. Not a caveat, not a question."""
    with st.container(border=True, key="hint", horizontal=True, wrap=False,
                      vertical_alignment="top"):
        st.markdown(":green[:material/lightbulb:]", width="content")
        st.markdown(text)


def questions(items, key):
    """Discussion prompts. style.py styles any container keyed `talk-*` amber."""
    with st.container(border=True, key="talk-" + key):
        st.caption("Talk it through")
        st.markdown("\n".join(items))


def cutoff_in_use():
    """Restate the step-1 cut-off on any page whose numbers depend on it.

    The models on the Train page are fitted to labels the user chose two
    pages back. Without this the AUROC has no stated basis, and changing the
    cut-off silently changes every score.
    """
    dt = binarize(training_data(), st.session_state["cutoff"], HIGHER_IS_ACTIVE)
    n_active = int(dt["Binary"].sum())
    with st.container(border=True, key="cutoff-in-use"):
        st.caption("Cut-off in use")
        st.markdown(
            "You set this on the **Data** page: compounds scoring **{0:.1f}** {1} on {2} "
            "count as active. That is **{3:,}** actives against **{4:,}** inactives - "
            "both models below are fitted to those labels.".format(
                st.session_state["cutoff"],
                "or above" if HIGHER_IS_ACTIVE else "or below",
                READOUT_LABEL.lower(), n_active, len(dt) - n_active,
            )
        )


def advance(key, url_path, label, icon=":material/arrow_forward:"):
    """Unlock the next page and go there. Remembered for the rest of the session.

    Setting the flag is not enough on its own. app.py builds the navigation
    from these flags *before* it runs the page body that contains this button,
    so on the click itself the new page is not in the nav yet and nothing
    visibly happens - which is why the button used to need two clicks. The
    rerun rebuilds the nav; `goto` asks app.py to land on the page the label
    promises, once that page exists.
    """
    if st.session_state.get(key):
        return True
    if st.button(label, key="button_" + key, icon=icon, type="primary"):
        st.session_state[key] = True
        st.session_state["goto"] = url_path
        st.rerun()
    return False


def training_data():
    return cached_training_data(TRAINING_FILE)


def default_cutoff(values):
    """Where the slider starts. The mean, unless info.py pins a value."""
    if CUTOFF_DEFAULT is not None:
        return float(CUTOFF_DEFAULT)
    mean = round(values.mean() / CUTOFF_STEP) * CUTOFF_STEP
    return float(min(max(mean, CUTOFF_MIN), CUTOFF_MAX))


def binary_labels():
    return list(binarize(training_data(), st.session_state["cutoff"], HIGHER_IS_ACTIVE)["Binary"])


# --- Step 1 ------------------------------------------------------------------

def understand_the_data():
    df = training_data()
    heading("understand_the_data")
    st.link_button(
        "Open the assay record on ECBD", ECBD_ASSAY_URL, icon=":material/open_in_new:"
    )
    cols = st.columns([2, 1], gap="medium")
    cols[0].dataframe(df[[SMILES_COLUMN, READOUT_COLUMN]], height=460)
    with cols[1]:
        questions(q1, "q1")

    st.divider()
    choose_a_cutoff()
    models_used("understand_the_data")


# --- Step 2 ------------------------------------------------------------------

def choose_a_cutoff():
    df = training_data()
    heading("choose_a_cutoff")

    with st.container(border=True, key="card-cutoff"):
        # The slider is the control; the four numbers are what it produces. Side
        # by side in one row of five, the slider reads as a fifth metric that has
        # gone wrong - its label, value and track all sit on different baselines
        # from the numbers. Stacked, the control leads and the numbers align.
        cutoff = st.slider(
            "Activity cut-off", CUTOFF_MIN, CUTOFF_MAX,
            default_cutoff(df[READOUT_COLUMN]), CUTOFF_STEP, format="%.1f",
            width=520,
        )
        dt = binarize(df, cutoff, HIGHER_IS_ACTIVE)
        stats = st.columns(4)
        stats[0].metric("Mean", round(df[READOUT_COLUMN].mean(), 2))
        stats[1].metric("Std deviation", round(df[READOUT_COLUMN].std(), 2))
        stats[2].metric("Actives", int(dt["Binary"].sum()))
        stats[3].metric("Inactives", int(len(dt) - dt["Binary"].sum()),
                        help=SAMPLING_CAVEAT)

    cols = st.columns(2, gap="medium")
    cols[0].caption(
        "Distribution of {0}, scaled back to the whole screen. The bars are "
        "square-root scaled, so the tail stays visible.".format(READOUT_LABEL.lower())
    )
    cols[0].altair_chart(
        plot_readout_histogram(
            screen_scale(dt, READOUT_COLUMN), READOUT_COLUMN, cutoff, READOUT_LABEL,
            weight_column="Weight", count_label="Share of the screen (%)", share=True,
        ),
        width="stretch",
    )
    cols[1].caption("t-SNE projection onto Ersilia's reference chemical space")
    if os.path.exists(data_path(PROJECTION_FILE)):
        cols[1].altair_chart(
            plot_chemical_space(
                cached_projection(PROJECTION_FILE), PROJECTION_X, PROJECTION_Y, dt["Binary"]
            ),
            width="stretch",
        )
    else:
        cols[1].warning("Missing `data/{0}`.".format(PROJECTION_FILE))

    questions(q2, "q2")

    if st.button("Use this cut-off", icon=":material/check:", type="primary"):
        if st.session_state.get("cutoff") != cutoff:
            # Anything fitted against the old labels is now stale.
            for key in ("features", "models", "predictions"):
                st.session_state[key].clear()
        st.session_state["cutoff"] = cutoff
        st.session_state["cutoff_set"] = True
        st.rerun()

    if st.session_state.get("cutoff") is not None:
        st.success("Cut-off in use: {0}".format(st.session_state["cutoff"]))


# --- Step 3 ------------------------------------------------------------------

def train_a_model():
    if st.session_state.get("cutoff") is None:
        st.info("Choose a cut-off first.", icon=":material/info:")
        return

    y = binary_labels()
    heading("train_a_model")
    cutoff_in_use()

    cols = st.columns(len(DESCRIPTORS), gap="medium")
    for i, (label, filename) in enumerate(DESCRIPTORS.items()):
        with cols[i].container(border=True, key="card-descriptor-" + label):
            st.markdown("**{0}**".format(label))
            if st.button("Train a model", key="train_" + label, icon=":material/play_arrow:"):
                if not os.path.exists(data_path(filename)):
                    st.warning("Missing `data/{0}`.".format(filename))
                else:
                    with st.spinner("Calculating {0} and training...".format(label)):
                        X = cached_descriptors(filename)
                        st.session_state["features"][label] = {
                            "preview": descriptor_preview(X), "shape": X.shape,
                        }
                        st.session_state["models"][label] = train_classifier(X, y)
            if label in st.session_state["models"]:
                feature = st.session_state["features"][label]
                st.caption("One molecule, as {0} numbers".format(feature["shape"][1]))
                st.code(feature["preview"], language=None)
                aurocs = st.session_state["models"][label]["aurocs"]
                st.metric("AUROC", "{0:.3f} ± {1:.3f}".format(np.mean(aurocs), np.std(aurocs)))
                cv_data = st.session_state["models"][label]["cv_data"]
                panes = st.columns(2, gap="small")
                panes[0].caption("ROC, five folds")
                panes[0].altair_chart(plot_roc(interpolate_roc_curves(cv_data)), width="stretch")
                panes[1].caption("Scores on one fold")
                panes[1].altair_chart(plot_fold_scores(*cv_data[0]), width="stretch")

    questions(q3, "q3")
    models_used("train_a_model")
    if st.session_state["models"]:
        advance("step3", "screen", "Let's apply the models to a virtual screening exercise!")


# --- Step 4 ------------------------------------------------------------------

def screen_a_library():
    heading("screen_a_library")
    st.caption("Pick the library your group was assigned.")

    with st.container(horizontal=True, gap="small"):
        for i, filename in enumerate(LIBRARY_FILES):
            with st.container(key="lib-{0}".format(i + 1), width="content"):
                if st.button("Library {0}".format(i + 1), key="pick-{0}".format(i + 1)):
                    st.session_state["library"] = filename
                    st.rerun()

    if not st.session_state.get("library"):
        return

    library = cached_library(st.session_state["library"])
    st.success("Screening **{0}** - {1} compounds.".format(
        st.session_state["library"].replace(".csv", "").replace("_", " ").title(), len(library)))

    ranked = library.sort_values(ACTIVITY_MODEL_COLUMN, ascending=False)
    top = ranked.head(N_TOP_HITS)
    bottom = ranked.tail(N_TOP_HITS).iloc[::-1]          # worst first

    st.caption(
        "Predicted S. aureus bioactivity across the library, ChEMBL model. The line "
        "marks where the top {0} begins.".format(N_TOP_HITS)
    )
    st.altair_chart(
        plot_score_distribution(
            library[ACTIVITY_MODEL_COLUMN], "Predicted activity",
            marker=float(top[ACTIVITY_MODEL_COLUMN].min()),
        ),
        width="stretch",
    )

    panels = st.tabs(["Top {0}".format(N_TOP_HITS), "Bottom {0}".format(N_TOP_HITS)])
    for panel, subset in zip(panels, (top, bottom)):
        with panel:
            st.caption("Captions are the predicted activity.")
            draw_molecules_grid(
                list(subset[LIBRARY_SMILES_COLUMN]),
                ["{0:.2f}".format(v) for v in subset[ACTIVITY_MODEL_COLUMN]],
                per_row=8, size=(170, 150),
            )

    questions(q4, "q4")
    models_used("screen_a_library")
    advance("step4", "results", "See everything we know about them")


# --- Step 5 ------------------------------------------------------------------

def the_full_picture():
    if not st.session_state.get("library"):
        st.info("Pick a library first.", icon=":material/info:")
        return

    library = cached_library(st.session_state["library"])
    heading("the_full_picture")
    hint(RESULTS_HINT)

    table = library.sort_values(ACTIVITY_MODEL_COLUMN, ascending=False).rename(columns={
        LIBRARY_SMILES_COLUMN: "smiles",
        ACTIVITY_MODEL_COLUMN: ACTIVITY_MODEL_LABEL,
        **COLUMN_LABELS,
    })
    table = table[["smiles", ACTIVITY_MODEL_LABEL] + list(COLUMN_LABELS.values())]
    st.dataframe(table, height=430)
    st.download_button(
        "Download this table", table.to_csv(index=False).encode(),
        file_name=st.session_state["library"].replace(".csv", "_predictions.csv"),
        mime="text/csv", icon=":material/download:",
    )
    questions(q5, "q5")
    models_used("the_full_picture")
    advance("step5", "expand", "Let's expand one of the hits!")


# --- Step 6 ------------------------------------------------------------------

def hit_expansion():
    heading("hit_expansion")
    analogues = cached_analogues(ANALOGUES_FILE)
    analogues = analogues[analogues["generator"].isin(ANALOGUE_GENERATORS)]

    # 1. The hit ---------------------------------------------------------------
    cols = st.columns([0.32, 0.68], gap="medium")
    with cols[0].container(border=True, key="card-parent"):
        draw_molecule(PARENT_SMILES, size=(300, 250))
        st.markdown("**{0}**".format(PARENT_NAME))
        # Side by side: stacked, the card ran twice the height of the two
        # paragraphs beside it and left a hole in the right-hand column.
        parent_stats = st.columns(2)
        parent_stats[0].metric("S. aureus activity", PARENT_SAUREUS)
        parent_stats[1].metric("Efflux evasion", PARENT_EFFLUX)
    cols[1].markdown(PARENT_BLURB)
    cols[1].markdown(
        "To improve it we asked two generative models for analogues. Neither invents "
        "molecules freely: each is given a starting point and a rule about what it may "
        "change. **What you give them decides what you get back.**"
    )

    # 2. The generators --------------------------------------------------------
    st.divider()
    st.subheader("Two generators, two different inputs")
    gen_cols = st.columns(len(GENERATORS), gap="medium")
    for col, generator in zip(gen_cols, GENERATORS):
        with col.container(border=True, key="card-generator-" + generator["name"]):
            st.markdown("**{0}**  `{1}`".format(generator["name"], generator["model"]))
            st.caption(generator["input_label"])
            draw_molecule(generator["input_smiles"], size=(360, 230))
            st.caption(generator["text"])

    for generator in GENERATORS:
        subset = analogues[analogues["generator"] == generator["name"]]
        top = subset.sort_values(ANALOGUE_X, ascending=False).head(N_GENERATOR_EXAMPLES)
        with st.container(border=True, key="card-grid-" + generator["name"]):
            st.markdown("**{0}** - {1} analogues. Best {2} by predicted S. aureus "
                        "activity:".format(generator["name"], len(subset), N_GENERATOR_EXAMPLES))
            draw_molecules_grid(
                list(top["canonical_smiles"]),
                ["{0:.2f}".format(v) for v in top[ANALOGUE_X]],
                per_row=5, size=(190, 165),
            )
            st.download_button(
                "Download all {0} analogues as SMILES".format(generator["name"]),
                "\n".join(subset["canonical_smiles"]).encode(),
                file_name="{0}_analogues.smi".format(generator["name"].lower()),
                icon=":material/download:", key="dl_" + generator["name"],
            )

    # 3. Efflux ----------------------------------------------------------------
    st.divider()
    st.subheader("Getting inside a Gram-negative cell")
    st.markdown(EFFLUX_BLURB.format(PARENT_EFFLUX))
    st.caption(
        "{0} analogues. Up and to the right of the parent is better on both axes.".format(
            len(analogues))
    )
    st.altair_chart(
        plot_pareto(analogues, ANALOGUE_X, ANALOGUE_Y, ANALOGUE_SHORTLIST,
                    PARENT_SAUREUS, PARENT_EFFLUX, SAUREUS_THRESHOLD),
        width="stretch",
    )
    with st.container(border=True, key="card-shortlist"):
        cols = st.columns(4)
        cols[0].metric("Analogues", len(analogues))
        cols[1].metric("Keep potency", int(analogues["clears_saureus_thr"].sum()))
        cols[2].metric("Gain permeability", int(analogues["better_efflux_than_parent"].sum()))
        cols[3].metric("Both", int(analogues[ANALOGUE_SHORTLIST].sum()))

    # 4. Gram-negative activity ------------------------------------------------
    st.divider()
    st.subheader("Did any of it buy Gram-negative activity?")
    st.markdown(
        "Evading efflux is necessary, not sufficient. These two models predict growth "
        "inhibition directly, each with its own recommended threshold. Platensimycin "
        "fails both."
    )
    cols = st.columns(len(GRAM_NEGATIVE), gap="medium")
    for col, (name, column, threshold, parent, model) in zip(cols, GRAM_NEGATIVE):
        clearing = int((analogues[column] >= threshold).sum())
        with col.container(border=True, key="card-gramneg-" + name):
            st.markdown("**{0}**  `{1}`".format(name, model))
            st.caption("Threshold {0}. Platensimycin scores {1}.".format(threshold, parent))
            st.altair_chart(
                plot_score_distribution(analogues[column], "Predicted activity",
                                        marker=threshold),
                width="stretch",
            )
            st.metric("Analogues clearing the threshold", clearing)

    questions(q6, "q6")
    models_used("hit_expansion")
