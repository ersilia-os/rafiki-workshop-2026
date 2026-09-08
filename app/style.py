"""The few things Streamlit's theme config cannot reach.

Everything else lives in .streamlit/config.toml. Keep this short: the top-nav
rules target Streamlit's own class names, which can change between releases.
The active tab is found via aria-current="page", which Streamlit sets itself.
"""

PLUM = "#50285A"
PERIWINKLE = "#6C5CE7"
NOTE_TINT = "#FDF7EA"   # brand yellow, tinted: reads as a margin note
NOTE_EDGE = "#EFDFB8"
SURFACE = "#FFFFFF"
EDGE = "#E6E6EE"
INK = "#2C3E50"

from info import LIBRARY_COLOURS

# One rule per library button, so each carries its own colour.
LIBRARY_RULES = "".join("""
.st-key-lib-{i} button {{
    background: {c} !important;
    border-color: {c} !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
}}
.st-key-lib-{i} button p {{ color: #FFFFFF !important; }}
.st-key-lib-{i} button:hover {{ filter: brightness(1.12); }}
""".format(i=i + 1, c=c) for i, c in enumerate(LIBRARY_COLOURS))

CSS = """
<style>
/* --- Top navigation ------------------------------------------------------
   The tab bar is the only signpost now the steps are separate pages, so it has
   to read from the back of a room. Tabs become pills; the active one goes plum. */
[data-testid="stTopNavSection"] {
    padding-block: 0.4rem !important;
    border-bottom: 2px solid %(edge)s !important;
}
[data-testid="stTopNavLinkContainer"], .stTopNavLinkContainer {
    gap: 0.5rem !important;
}
[data-testid="stTopNavLink"], .stTopNavLink {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    padding: 0.6rem 1.25rem !important;
    border-radius: 999px !important;
    border: 1px solid %(edge)s !important;
    background: %(surface)s !important;
    color: %(ink)s !important;
    letter-spacing: 0 !important;
    transition: none !important;
}
[data-testid="stTopNavLink"] p, .stTopNavLink p {
    font-size: 1.15rem !important;
    font-weight: 600 !important;
    margin: 0 !important;
}
[data-testid="stTopNavLink"]:hover, .stTopNavLink:hover {
    border-color: %(periwinkle)s !important;
    color: %(periwinkle)s !important;
}

/* The page you are on. Streamlit sets aria-current itself. */
[aria-current="page"] [data-testid="stTopNavLink"],
[data-testid="stTopNavLink"][aria-current="page"],
a[aria-current="page"] {
    background: %(plum)s !important;
    border-color: %(plum)s !important;
    color: #FFFFFF !important;
}
[aria-current="page"] [data-testid="stTopNavLink"] p,
[data-testid="stTopNavLink"][aria-current="page"] p,
a[aria-current="page"] p,
a[aria-current="page"] span {
    color: #FFFFFF !important;
}

/* --- Discussion prompt ---------------------------------------------------
   Warm sand rather than the blue info box every other Ersilia app uses. */
[class*="st-key-talk"] {
    background: %(note)s !important;
    border-color: %(note_edge)s !important;
    border-radius: 0.75rem !important;
}
[class*="st-key-talk"] [data-testid="stCaptionContainer"] p {
    color: %(plum)s !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}

/* A reading hint. Third box type, so it is not mistaken for either of the others. */
.st-key-hint {
    background: #F1F8ED !important;
    border-color: #CFE7C2 !important;
    border-radius: 0.75rem !important;
}

/* A caveat, kept visually distinct from the discussion prompt. */
.st-key-careful {
    background: #F1EFFC !important;
    border-color: #D9D3F5 !important;
    border-radius: 0.75rem !important;
}
.st-key-careful p { color: %(plum)s !important; }

/* --- Step marker ---------------------------------------------------------
   A belt-and-braces "where am I", independent of the nav styling above. */
.st-key-eyebrow p {
    color: %(plum)s !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
}
%(libraries)s
</style>
""" % {
    "plum": PLUM, "periwinkle": PERIWINKLE, "note": NOTE_TINT, "note_edge": NOTE_EDGE, "libraries": LIBRARY_RULES,
    "surface": SURFACE, "edge": EDGE, "ink": INK,
}
