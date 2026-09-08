"""One function per step. Each is registered as a page in app.py."""

import os
import random
import time

import numpy as np
import streamlit as st

from cache import (
    cached_analogues, cached_library, cached_projection,
    cached_catalogue, cached_pretrained, cached_rafiki_ids, cached_responses,
    cached_training_data, clear_responses,
)
from info import (
    ACTIVITY_MODEL_COLUMN, ACTIVITY_MODEL_LABEL, ANALOGUES_FILE, ANALOGUE_GENERATORS,
    ANALOGUE_SHORTLIST, ANALOGUE_X, ANALOGUE_Y, EFFLUX_BLURB, GENERATORS,
    GRAM_NEGATIVE, N_GENERATOR_EXAMPLES, PARENT_BLURB,
    COLUMN_LABELS, CUTOFF_DEFAULT, CUTOFF_MAX, CUTOFF_MIN, CUTOFF_STEP, DESCRIPTORS,
    HIGHER_IS_ACTIVE, LIBRARY_FILES, LIBRARY_SMILES_COLUMN, N_TOP_HITS,
    CLOSING, CLOSING_TITLE, FORM_RESPONSES_URL, PICKS_FORM_URL,
    N_COLLECTIVE_SHOWN, N_SCREEN_PREVIEW, READOUT_TABLE_LABEL,
    RESPONSE_CANDIDATE_COLUMNS, SCREENING_SECONDS, SMILES_LABEL,
    PARENT_EFFLUX, PARENT_NAME, PARENT_SAUREUS, PARENT_SMILES, PRETRAINED_FILE,
    PROJECTION_FILE,
    RAFIKI_IDS_FILE, RAFIKI_ID_LABEL,
    PROJECTION_X, PROJECTION_Y, READOUT_COLUMN, READOUT_LABEL, SAUREUS_THRESHOLD,
    MODELS, MODEL_HUB_URL, NATURAL_PRODUCTS_NOTE, N_PROFILE_SHOWN,
    PROFILING_INTRO, SAMPLING_CAVEAT, SMILES_COLUMN, STEP_MODELS, STEP_TEXT,
    TRAINING_FILE, ECBD_ASSAY_URL,
    TRAINING_SECONDS, TRAINING_STEPS,
    q1, q2, q3, q4, q5, q6, q7,
)
from plots import (
    plot_chemical_space, plot_fold_scores, plot_pareto, plot_readout_histogram, plot_roc,
    plot_score_distribution,
)
from molecules import draw_molecule, draw_molecules_grid
from utils import (
    binarize, data_path,
    normalise_rafiki_id, pretrained_at, screen_scale,
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
    with st.expander("Relevant Ersilia Model Hub models", icon=":material/deployed_code:"):
        st.markdown(listed)
        st.caption("[Browse the Ersilia Model Hub]({0})".format(MODEL_HUB_URL))


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


def _filter_and_sort(table, columns, identifier):
    """Sorting and per-column filters, folded away above the table.

    Sorting lives here rather than in the dataframe's own headers because that
    sorting is client side: Streamlit never learns about it, so the structures
    drawn underneath would keep showing the first rows in the frame's order
    while the table showed something else.

    Laid out in three blocks - order, ranges, flags - because interleaving
    sliders and toggles by column made a jumble.
    """
    # A flag is a column whose values are only 0 and 1. Everything else takes a
    # range. Testing the other way round - a strict superset of {0, 1} - looks
    # equivalent and is not: a score running 0.245 to 0.923 contains neither.
    flags = [c for c in columns if set(table[c].dropna().unique()) <= {0, 1}]
    numeric = [c for c in columns if c not in flags]
    shown = table

    with st.expander("Filter and sort the table", icon=":material/filter_list:"):
        order = st.columns(4)
        by = order[0].selectbox("Sort by", [identifier] + numeric + flags, key="sort_by")
        descending = order[1].segmented_control(
            "Order", ["Ascending", "Descending"], default="Ascending", key="sort_dir",
        ) == "Descending"

        st.caption("Ranges")
        grid = st.columns(4)
        for i, name in enumerate(numeric):
            low, high = float(table[name].min()), float(table[name].max())
            if low == high:
                continue
            span = grid[i % 4].slider(name, low, high, (low, high), key="range_" + name)
            shown = shown[shown[name].between(*span)]

        st.caption("Flags")
        row = st.columns(4)
        for i, name in enumerate(flags):
            choice = row[i % 4].segmented_control(
                name, ["Any", "Yes", "No"], default="Any", key="flag_" + name)
            if choice == "Yes":
                shown = shown[shown[name] == 1]
            elif choice == "No":
                shown = shown[shown[name] == 0]

    return shown.sort_values(by, ascending=not descending)


def _run_predictions():
    """Play out the screening run. The scores themselves are columns the library
    already carries; this is the pacing, so a room sees it happen."""
    bar = st.progress(0.0, text="{0} · {1}".format(
        ACTIVITY_MODEL_COLUMN.split("_")[0], ACTIVITY_MODEL_LABEL))
    ticks = 20
    for i in range(ticks):
        time.sleep(SCREENING_SECONDS / ticks)
        bar.progress((i + 1) / ticks)
    bar.empty()


def _method_lines(label, result, meta):
    """How the numbers were produced. Every line is a statement about the run
    that produced this AUROC; none says work is happening now."""
    facts = {
        "descriptor": label,
        "n_features": result["shape"][1],
        "n_trees": meta["n_trees"],
        "n_splits": meta["n_splits"],
        "test_pct": int(round(meta["test_size"] * 100)),
    }
    return [step.format(**facts) for step in TRAINING_STEPS]


def _reveal_method(label, lines):
    """Walk the method a line at a time, then hand over to the marker that
    stays. A result that lands instantly gives a room nothing to look at."""
    pause = TRAINING_SECONDS / len(lines)
    with st.status("Fitting {0}".format(label), expanded=True) as status:
        for line in lines:
            st.write(line)
            time.sleep(pause)
        status.update(label="Trained on {0}".format(label), state="complete",
                      expanded=False)


def cutoff_in_use():
    """Restate the step-1 cut-off on any page whose numbers depend on it.

    The models on the Train page are fitted to labels the user chose two
    pages back. Without this the AUROC has no stated basis, and changing the
    cut-off silently changes every score.
    """
    dt = binarize(training_data(), st.session_state["cutoff"], HIGHER_IS_ACTIVE)
    n_active = int(dt["Binary"].sum())
    st.markdown(
        "You set this on the **Data** page: compounds scoring **{0:.1f}** {1} on {2} "
        "count as active. That is **{3:,}** actives against **{4:,}** inactives - "
        "both models below are fitted to those labels.".format(
            st.session_state["cutoff"],
            "or above" if HIGHER_IS_ACTIVE else "or below",
            READOUT_LABEL.lower(), n_active, len(dt) - n_active,
        )
    )


def advance(key, url_path, label, icon=":material/arrow_forward:", kind="primary"):
    """Unlock the next page and go there.

    Shown whenever the page is, including after it has been used: it used to
    hide itself once the flag was set, which meant the way onward vanished from
    any page you came back to.

    Setting the flag is not enough on its own. app.py builds the navigation
    from these flags *before* it runs the page body that contains this button,
    so on the click itself the new page is not in the nav yet and nothing
    visibly happens - which is why the button once needed two clicks. The rerun
    rebuilds the nav; `goto` asks app.py to land on the page the label promises,
    once that page exists.
    """
    if st.button(label, key="button_" + key, icon=icon, type=kind):
        st.session_state[key] = True
        st.session_state["goto"] = url_path
        st.rerun()


def training_data():
    return cached_training_data(TRAINING_FILE)


def default_cutoff(values):
    """Where the slider starts. The mean, unless info.py pins a value."""
    if CUTOFF_DEFAULT is not None:
        return float(CUTOFF_DEFAULT)
    mean = round(values.mean() / CUTOFF_STEP) * CUTOFF_STEP
    return float(min(max(mean, CUTOFF_MIN), CUTOFF_MAX))


# --- Step 1 ------------------------------------------------------------------

def understand_the_data():
    df = training_data()
    heading("understand_the_data")
    st.link_button(
        "Open the assay record on ECBD", ECBD_ASSAY_URL, icon=":material/open_in_new:"
    )
    cols = st.columns([2, 1], gap="medium")
    cols[0].dataframe(
        df[[SMILES_COLUMN, READOUT_COLUMN]].rename(
            columns={SMILES_COLUMN: SMILES_LABEL, READOUT_COLUMN: READOUT_TABLE_LABEL}
        ),
        height=460,
    )
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
    cols[0].caption("Distribution of {0}".format(READOUT_LABEL.lower()))
    cols[0].altair_chart(
        plot_readout_histogram(
            screen_scale(dt, READOUT_COLUMN), READOUT_COLUMN, cutoff, READOUT_LABEL,
            weight_column="Weight", count_label="Share of the screen (%)", share=True,
        ),
        width="stretch",
    )
    cols[1].caption("Chemical space visualization of the screening library")
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

    # One button, not two: accepting the cut-off and going to train it is a
    # single decision. The badge beside it says what is already in use, which
    # matters when someone comes back to this page to change their mind.
    with st.container(horizontal=True, wrap=False, vertical_alignment="center"):
        if st.button("Ready to train a model!", icon=":material/arrow_forward:",
                     type="primary"):
            if st.session_state.get("cutoff") != cutoff:
                # Anything fitted against the old labels is now stale.
                for key in ("features", "models", "predictions"):
                    st.session_state[key].clear()
            st.session_state["cutoff"] = cutoff
            st.session_state["cutoff_set"] = True
            st.session_state["goto"] = "train"
            st.rerun()
        if st.session_state.get("cutoff") is not None:
            st.badge(
                "Cut-off in use: {0:.1f}".format(st.session_state["cutoff"]),
                color="green", icon=":material/check_circle:",
            )


# --- Step 3 ------------------------------------------------------------------

def train_a_model():
    if st.session_state.get("cutoff") is None:
        st.info("Choose a cut-off first.", icon=":material/info:")
        return

    heading("train_a_model")
    cutoff_in_use()

    if not os.path.exists(data_path(PRETRAINED_FILE)):
        st.error(
            "Missing `data/{0}`. Build it with `python scripts/06_pretrain_models.py`.".format(
                PRETRAINED_FILE
            ),
            icon=":material/error:",
        )
        return
    grid = cached_pretrained(PRETRAINED_FILE)

    cols = st.columns(len(DESCRIPTORS), gap="medium")
    for i, label in enumerate(DESCRIPTORS):
        with cols[i].container(border=True, key="card-descriptor-" + label):
            st.markdown("**{0}**".format(label))
            if st.button("Train a model", key="train_" + label, icon=":material/play_arrow:"):
                result = pretrained_at(grid, label, st.session_state["cutoff"])
                if result is None:
                    st.warning(
                        "No run stored for a cut-off of {0:.0f}.".format(
                            st.session_state["cutoff"]),
                        icon=":material/help:",
                    )
                else:
                    _reveal_method(label, _method_lines(label, result, grid["meta"]))
                    st.session_state["models"][label] = result
                    # Rerun so the marker below replaces the reveal. Without it the
                    # status belongs to this run only, and training the second
                    # descriptor would make the first one's disappear.
                    st.rerun()
            if label in st.session_state["models"]:
                result = st.session_state["models"][label]
                with st.status("Trained on {0}".format(label), state="complete",
                               expanded=False):
                    for line in _method_lines(label, result, grid["meta"]):
                        st.write(line)
                aurocs = result["aurocs"]
                st.metric("AUROC", "{0:.3f} ± {1:.3f}".format(np.mean(aurocs), np.std(aurocs)))
                panes = st.columns(2, gap="small")
                panes[0].caption("ROC, five folds")
                panes[0].altair_chart(plot_roc(result["curves"]), width="stretch")
                panes[1].caption("Scores on one fold")
                panes[1].altair_chart(plot_fold_scores(*result["fold"]), width="stretch")

    questions(q3, "q3")
    if st.session_state["models"]:
        advance("step3", "screen", "Let's apply the models to a virtual screening exercise!")
    models_used("train_a_model")


# --- Step 4 ------------------------------------------------------------------

def screen_a_library():
    heading("screen_a_library")
    st.caption("Select a library. There is no good or bad choice")

    with st.container(horizontal=True, gap="small"):
        for i, filename in enumerate(LIBRARY_FILES):
            with st.container(key="lib-{0}".format(i + 1), width="content"):
                if st.button("Library {0}".format(i + 1), key="pick-{0}".format(i + 1)):
                    st.session_state["library"] = filename
                    # A fresh face every time a library is pressed, including the
                    # same one twice. Seeded rather than re-drawn on each rerun,
                    # so pressing anything else on the page leaves it alone.
                    st.session_state["sample_seed"] = random.randrange(2 ** 32)
                    st.rerun()

    if not st.session_state.get("library"):
        return

    library = cached_library(st.session_state["library"])
    st.success("Screening **{0}** - {1} compounds.".format(
        st.session_state["library"].replace(".csv", "").replace("_", " ").title(), len(library)))

    # A look at the library before any score exists, captioned by identifier
    # rather than by prediction: there is nothing to rank on yet.
    ids = cached_rafiki_ids(RAFIKI_IDS_FILE).rename(
        columns={"rafiki_id": RAFIKI_ID_LABEL, "smiles": LIBRARY_SMILES_COLUMN})
    sample = library.merge(ids, on=LIBRARY_SMILES_COLUMN, how="left").sample(
        N_SCREEN_PREVIEW, random_state=st.session_state.get("sample_seed"),
    )
    st.caption("{0} of them, picked at random.".format(N_SCREEN_PREVIEW))
    draw_molecules_grid(
        list(sample[LIBRARY_SMILES_COLUMN]),
        list(sample[RAFIKI_ID_LABEL].fillna("")),
        per_row=8, size=(170, 150),
    )

    if st.session_state.get("screened") != st.session_state["library"]:
        if st.button("Run *Staphylococcus aureus* activity predictions",
                     icon=":material/play_arrow:", type="primary"):
            _run_predictions()
            st.session_state["screened"] = st.session_state["library"]
            st.rerun()
        models_used("screen_a_library")
        return

    st.subheader("Screening results")
    st.caption("{0} across the library.".format(ACTIVITY_MODEL_LABEL))
    st.altair_chart(
        plot_score_distribution(library[ACTIVITY_MODEL_COLUMN], "Activity score"),
        width="stretch",
    )

    top = library.merge(ids, on=LIBRARY_SMILES_COLUMN, how="left").sort_values(
        ACTIVITY_MODEL_COLUMN, ascending=False).head(N_TOP_HITS)
    st.caption("The {0} highest scoring.".format(N_TOP_HITS))
    draw_molecules_grid(
        list(top[LIBRARY_SMILES_COLUMN]),
        ["{0} · {1:.2f}".format(r[RAFIKI_ID_LABEL], r[ACTIVITY_MODEL_COLUMN])
         for _, r in top.iterrows()],
        per_row=8, size=(170, 150),
    )

    questions(q4, "q4")
    advance("step4", "profiling", "Get a richer profile of molecules")
    models_used("screen_a_library")


# --- Step 5 ------------------------------------------------------------------

def the_full_picture():
    if not st.session_state.get("library"):
        st.info("Pick a library first.", icon=":material/info:")
        return

    library = cached_library(st.session_state["library"])
    heading("the_full_picture")
    st.markdown(PROFILING_INTRO)
    hint(NATURAL_PRODUCTS_NOTE)

    table = library.rename(columns={
        LIBRARY_SMILES_COLUMN: "smiles",
        ACTIVITY_MODEL_COLUMN: ACTIVITY_MODEL_LABEL,
        **COLUMN_LABELS,
    })
    ids = cached_rafiki_ids(RAFIKI_IDS_FILE).rename(columns={"rafiki_id": RAFIKI_ID_LABEL})
    table = table.merge(ids, on="smiles", how="left")

    # Ordered by identifier, which means ordered at random with respect to every
    # column here: scripts/04_assign_rafiki_ids.py shuffled the compounds before
    # numbering them. Deliberately not ranked by activity - the point of this
    # page is that activity is only the first column - and deliberately not
    # reshuffled per run, which would reorder the table under anyone reading it.
    table = table.sort_values(RAFIKI_ID_LABEL)
    table = table[
        [RAFIKI_ID_LABEL, "smiles", ACTIVITY_MODEL_LABEL] + list(COLUMN_LABELS.values())
    ].rename(columns={"smiles": SMILES_LABEL})
    shown = _filter_and_sort(
        table, [ACTIVITY_MODEL_LABEL] + list(COLUMN_LABELS.values()), RAFIKI_ID_LABEL)
    st.caption("{0} of {1} compounds".format(len(shown), len(table)))
    # Column selection is enabled only for its documented side effect: it turns
    # off the header's own sorting. That sorting is client side, so it would
    # reorder the table without reordering the structures drawn underneath. The
    # "Sort by" control above does the job where Python can see it.
    st.dataframe(
        shown, height=430, hide_index=True,
        on_select="rerun", selection_mode="single-column", key="profile_table",
    )
    st.download_button(
        "Download full table", table.to_csv(index=False).encode(),
        file_name=st.session_state["library"].replace(".csv", "_predictions.csv"),
        mime="text/csv", icon=":material/download:",
    )

    top = shown.head(N_PROFILE_SHOWN)
    if len(top):
        st.caption("The first {0} in the table above.".format(len(top)))
        draw_molecules_grid(
            list(top[SMILES_LABEL]), list(top[RAFIKI_ID_LABEL].fillna("")),
            per_row=8, size=(170, 150),
        )

    questions(q5, "q5")
    # Submitting is what this page is for, so it keeps the periwinkle. Moving on
    # is the quieter of the two, which is how they stay distinguishable.
    st.link_button(
        "Submit your five candidates", PICKS_FORM_URL,
        icon=":material/open_in_new:", type="primary",
    )
    advance("step5", "collective", "See what everyone else picked", kind="secondary")
    models_used("the_full_picture")


def collective_picks():
    heading("collective_picks")

    with st.container(horizontal=True, wrap=False, vertical_alignment="center"):
        if st.button("Collect responses", icon=":material/refresh:", type="primary"):
            clear_responses()
            st.rerun()
        placeholder = st.empty()

    try:
        responses, fetched_at = cached_responses(FORM_RESPONSES_URL)
    except Exception as error:                        # network, or the sheet moved
        placeholder.empty()
        st.warning(
            "Could not read the responses sheet. {0}".format(error),
            icon=":material/cloud_off:",
        )
        return
    placeholder.caption(
        "{0} response{1}, read at {2} UTC".format(
            len(responses), "" if len(responses) == 1 else "s",
            fetched_at.strftime("%H:%M:%S"),
        )
    )

    if responses.empty:
        st.info(
            "Nobody has submitted yet. Fill the form in on the Profiling step, then "
            "press Collect responses.",
            icon=":material/hourglass_empty:",
        )
        return

    # One row per nomination, so the same compound from two groups counts twice.
    present = [c for c in RESPONSE_CANDIDATE_COLUMNS if c in responses.columns]
    picks = responses.melt(value_vars=present, value_name="entry")["entry"].dropna()
    picks = picks.astype(str).str.strip()
    picks = picks[picks != ""]

    ids = cached_rafiki_ids(RAFIKI_IDS_FILE).rename(columns={"rafiki_id": RAFIKI_ID_LABEL})
    catalogue = cached_catalogue(
        LIBRARY_FILES, LIBRARY_SMILES_COLUMN, ACTIVITY_MODEL_COLUMN
    ).rename(columns={LIBRARY_SMILES_COLUMN: "smiles",
                      ACTIVITY_MODEL_COLUMN: ACTIVITY_MODEL_LABEL})

    # Valid means two things: it reads as an identifier, and it is one we issued.
    # RAFIKI-9999 passes the first test and fails the second, so both are checked
    # against the catalogue rather than the pattern alone. Anything else is
    # skipped and reported, never guessed at.
    issued = set(ids[RAFIKI_ID_LABEL])
    resolved = picks.map(normalise_rafiki_id)
    resolved = resolved.where(resolved.isin(issued))
    rejected = sorted(set(picks[resolved.isna()]))
    resolved = resolved.dropna()

    if resolved.empty:
        st.warning("None of the entries are identifiers we issued.", icon=":material/help:")
        return

    counts = (resolved.value_counts().rename_axis(RAFIKI_ID_LABEL)
              .reset_index(name="Nominations"))
    counts = counts.merge(ids, on=RAFIKI_ID_LABEL, how="left")
    counts = counts.merge(catalogue, on="smiles", how="left")

    stats = st.columns(4)
    stats[0].metric("Responses", len(responses))
    stats[1].metric("Nominations", int(len(resolved)))
    stats[2].metric("Distinct compounds", int(counts[RAFIKI_ID_LABEL].nunique()))
    stats[3].metric(
        "Picked more than once", int((counts["Nominations"] > 1).sum()),
        help="Compounds two or more groups arrived at independently.",
    )

    if rejected:
        st.warning(
            "Skipped, because these are not identifiers we issued: {0}".format(
                ", ".join(rejected[:12]) + ("..." if len(rejected) > 12 else "")
            ),
            icon=":material/help:",
        )

    shown = counts.head(N_COLLECTIVE_SHOWN)
    st.caption(
        "Every compound the room nominated, most-picked first."
        + ("" if len(shown) == len(counts)
           else " Showing the first {0} of {1}.".format(len(shown), len(counts)))
    )
    draw_molecules_grid(
        list(shown["smiles"]),
        ["{0} · picked {1}x".format(r[RAFIKI_ID_LABEL], r["Nominations"])
         for _, r in shown.iterrows()],
        per_row=5, size=(190, 165),
    )

    st.dataframe(
        counts[[RAFIKI_ID_LABEL, "Nominations", ACTIVITY_MODEL_LABEL, "smiles"]]
            .rename(columns={"smiles": SMILES_LABEL}),
        height=320, hide_index=True,
    )

    with st.expander("Who submitted what", icon=":material/list:"):
        st.dataframe(responses, hide_index=True)

    questions(q7, "q7")
    advance("step6", "expand", "Hit identified!")


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

    # The last step, so it ends the workshop rather than handing on to another
    # page. advance() is for unlocking a next step and there is not one.
    st.divider()
    st.subheader(CLOSING_TITLE)
    st.markdown(CLOSING)
