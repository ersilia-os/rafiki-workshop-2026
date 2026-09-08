import os
import sys

import streamlit as st

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root)

from info import (
    ORGANISATION, PAGES, READOUT_COLUMN, SMILES_COLUMN, TITLE, TRAINING_FILE,
    WORDMARK_LABEL,
)
from style import CSS, header_label, locked_tabs
from utils import data_path
import steps

FAVICON = os.path.join(root, "..", "assets", "favicon.png")
WORDMARK = os.path.join(root, "..", "assets", "ersilia_brand.png")

# No sidebar: the workshop is named beside the wordmark instead.
st.set_page_config(layout="wide", page_title=TITLE, page_icon=FAVICON)

st.session_state.setdefault("features", {})
st.session_state.setdefault("models", {})
st.session_state.setdefault("predictions", {})
st.session_state.setdefault("cutoff", None)
st.session_state.setdefault("cutoff_set", False)

# A page becomes reachable once the step before it has been completed.
UNLOCKS = {
    "train": "cutoff_set",
    "screen": "step3",
    "profiling": "step4",
    "expand": "step5",
}


# Set RAFIKI_UNLOCK_ALL=1 to reach every page without walking the workshop.
# Off by default, so a deployed app still gates the steps in order.
UNLOCK_ALL = os.environ.get("RAFIKI_UNLOCK_ALL") == "1"


def unlocked(url_path):
    if UNLOCK_ALL:
        return True
    key = UNLOCKS.get(url_path)
    return key is None or bool(st.session_state.get(key))


def render(spec, number):
    """Shared header, then the step itself.

    One quiet line. The nav names the step; this adds the position within the
    five, which the nav cannot show, and it survives the nav CSS going stale.
    """
    url_path, title, _, step = spec
    st.html(CSS)
    st.html(header_label(WORDMARK_LABEL))
    st.html(locked_tabs([p[0] for p in PAGES if not unlocked(p[0])]))
    with st.container(key="eyebrow", horizontal=True, vertical_alignment="center"):
        st.caption("Step {0} of {1} · {2}".format(number, len(PAGES), title))
        if UNLOCK_ALL:
            st.badge("all steps unlocked", color="orange", icon=":material/lock_open:")
    if not unlocked(url_path):
        # The tab is greyed and unclickable, but a typed URL still lands here.
        st.info("Finish step {0} first.".format(number - 1), icon=":material/lock:")
        return
    getattr(steps, step)()


def page(spec, number):
    url_path, title, icon, _ = spec
    return st.Page(
        lambda spec=spec, number=number: render(spec, number),
        title=title, icon=icon, url_path=url_path, default=url_path == PAGES[0][0],
    )


# Upper-left chrome, capped at 32px tall. style.header_label writes the
# workshop's name beside it.
st.logo(WORDMARK, size="large", link="https://ersilia.io")

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

# Every step is always in the nav, so the shape of the workshop is visible from
# the first screen. Locked ones are greyed and unclickable (style.locked_tabs)
# and refuse to render their body (render, above).
pages = [page(spec, i + 1) for i, spec in enumerate(PAGES)]
nav = st.navigation(pages, position="top")

# A step button unlocks the next page and parks its url_path here. It cannot
# switch to it itself: st.switch_page only accepts a page that is already in
# st.navigation, and on the click the unlock has not been seen yet. By this
# run it has.
goto = st.session_state.pop("goto", None)
target = next((p for p in pages if p.url_path == goto), None)
if target is not None:
    st.switch_page(target)

nav.run()
