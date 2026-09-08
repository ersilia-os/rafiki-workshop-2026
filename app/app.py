import os
import sys

import streamlit as st

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root)

from info import (
    ORGANISATION, PAGES, READOUT_COLUMN, SMILES_COLUMN, TITLE, TRAINING_FILE, intro,
)
from style import CSS
from utils import data_path
import steps

FAVICON = os.path.join(root, "..", "assets", "favicon.png")
WORDMARK = os.path.join(root, "..", "assets", "ersilia_brand.png")

st.set_page_config(
    layout="wide", page_title=TITLE, page_icon=FAVICON, initial_sidebar_state="collapsed"
)

st.session_state.setdefault("features", {})
st.session_state.setdefault("models", {})
st.session_state.setdefault("predictions", {})
st.session_state.setdefault("cutoff", None)
st.session_state.setdefault("cutoff_set", False)

# A page becomes reachable once the step before it has been completed.
UNLOCKS = {
    "train": "cutoff_set",
    "screen": "step3",
    "results": "step4",
    "expand": "step5",
}


# Set RAFIKI_UNLOCK_ALL=1 to reach every page without walking the workshop.
# Off by default, so a deployed app still gates the steps in order.
UNLOCK_ALL = os.environ.get("RAFIKI_UNLOCK_ALL") == "1"


def available(url_path):
    if UNLOCK_ALL:
        return True
    key = UNLOCKS.get(url_path)
    return key is None or bool(st.session_state.get(key))


def render(spec, number):
    """Shared header, then the step itself.

    The badge repeats what the nav already says. That is deliberate: the tab
    styling leans on Streamlit's own class names, and this does not.
    """
    _, title, _, step = spec
    st.html(CSS)
    with st.container(key="eyebrow", horizontal=True, vertical_alignment="center"):
        st.badge("Step {0} of {1} · {2}".format(number, len(PAGES), title), color="violet")
        st.caption("{0} · {1}".format(TITLE, ORGANISATION))
        if UNLOCK_ALL:
            st.badge("all steps unlocked", color="orange", icon=":material/lock_open:")
    getattr(steps, step)()


def page(spec, number):
    url_path, title, icon, _ = spec
    return st.Page(
        lambda spec=spec, number=number: render(spec, number),
        title=title, icon=icon, url_path=url_path, default=url_path == PAGES[0][0],
    )


with st.sidebar:
    st.image(WORDMARK, width="stretch")
    st.write(intro)
    st.caption("Questions: [hello@ersilia.io](mailto:hello@ersilia.io)")

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

st.navigation(
    [page(spec, i + 1) for i, spec in enumerate(PAGES) if available(spec[0])],
    position="top",
).run()
