import os
import sys

import streamlit as st

root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root)

from info import (
    ORGANISATION, PAGES, READOUT_COLUMN, SMILES_COLUMN, TITLE, TRAINING_FILE, intro,
)
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

# A page becomes reachable once the step before it has been completed.
UNLOCKS = {
    "cutoff": "step1",
    "train": "step1",
    "screen": "step3",
    "results": "step4",
    "expand": "step5",
}


def available(url_path):
    key = UNLOCKS.get(url_path)
    return key is None or bool(st.session_state.get(key))


def render(step):
    """Every page shares the same eyebrow, then runs its own step."""
    st.caption("{0} · {1}".format(TITLE, ORGANISATION))
    getattr(steps, step)()


def page(spec):
    url_path, title, icon, step = spec
    return st.Page(
        lambda step=step: render(step), title=title, icon=icon, url_path=url_path,
        default=url_path == PAGES[0][0],
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

st.navigation([page(spec) for spec in PAGES if available(spec[0])], position="top").run()
