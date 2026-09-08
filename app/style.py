"""The few things Streamlit's theme config cannot reach.

Everything else lives in .streamlit/config.toml. Keep this short: these rules
target Streamlit's own class names, which can change between releases. Two
hooks are stable enough to rely on - `aria-current="page"`, which Streamlit
sets itself, and the `st-key-*` class Streamlit derives from a widget `key`.
Anything selected by `data-testid` is the fragile part; check it after an
upgrade.

No plum here. Plum is the Ersilia identity - the wordmark, the favicon, the
reference lines on the charts - and it stays out of the chrome. Periwinkle
carries interaction, and everything that is not interactive stays neutral.

One idiom, used everywhere colour has to mean something: a light wash of the
hue, a hairline of the hue, and the label in the hue. Never a saturated fill.
That is the active nav tab, the six library buttons and the three callouts.
"""

def _css_string(text):
    """Quote a string for CSS `content`, escaping what would end it early."""
    return '"%s"' % text.replace("\\", "\\\\").replace('"', '\\"')


PERIWINKLE = "#6C5CE7"
TINT_SOFT = "rgba(108, 92, 231, 0.07)"   # periwinkle wash: hover and the current tab
SURFACE = "#FFFFFF"
RECESSED = "#F4F4F8"
EDGE = "#E6E6EE"
MUTED = "#6B6675"

# The three callout hues, from the design system's semantic tokens.
GUIDE = "#3F9D6B"     # how to read the page
DISCUSS = "#C98A1E"   # talk it through

from info import LIBRARY_COLOURS

# One rule per library button, so each carries its own colour. A workshop needs
# "click the green one" to work from the back of a room, but six saturated
# fills were the loudest thing in the app; the wash keeps them just as
# distinguishable and stops Library 6 reading as an error.
LIBRARY_RULES = "".join("""
.st-key-lib-{i} button {{
    background: color-mix(in srgb, {c} 12%, #FFFFFF) !important;
    border: 1px solid color-mix(in srgb, {c} 45%, #FFFFFF) !important;
    color: color-mix(in srgb, {c} 78%, #000000) !important;
    font-weight: 500 !important;
}}
.st-key-lib-{i} button p {{ color: inherit !important; }}
.st-key-lib-{i} button:hover {{
    background: color-mix(in srgb, {c} 20%, #FFFFFF) !important;
    border-color: {c} !important;
}}
""".format(i=i + 1, c=c) for i, c in enumerate(LIBRARY_COLOURS))

# The three callouts share one shape - recessed panel, hue only on the left
# edge and the glyph. Three pastel fills read as three unrelated components.
# The glyphs themselves are coloured in steps.py with Streamlit's own :red[]
# / :green[] directives, which resolve to the same theme colours as the
# edges here - a markdown :material/ icon carries no test id to hook.
CALLOUT_RULES = "".join("""
{sel} {{
    background: {bg} !important;
    border: 1px solid {edge} !important;
    border-left: 3px solid {hue} !important;
    border-radius: 0.75rem !important;
}}
{sel} [data-testid="stCaptionContainer"] p {{
    color: color-mix(in srgb, {hue} 82%, #000000) !important;
    font-weight: 600 !important;
    font-size: 0.8rem !important;
}}
""".format(sel=sel, hue=hue, bg=RECESSED, edge=EDGE) for sel, hue in (
    (".st-key-hint", GUIDE),
    ('[class*="st-key-talk"]', DISCUSS),
    # A parameter carried over from an earlier step: state, so periwinkle.
    (".st-key-cutoff-in-use", PERIWINKLE),
))

CSS = """
<style>
/* --- Top navigation ------------------------------------------------------
   A filled pill reads as a button you should press rather than as where you
   already are. Quiet text; the current page takes the accent, a faint wash
   and a 2px rule underneath. */
[data-testid="stTopNavLinkContainer"], .stTopNavLinkContainer {
    gap: 0.25rem !important;
}
[data-testid="stTopNavLink"], .stTopNavLink {
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.85rem !important;
    /* Square bottom corners, so the underline reads as a tab and not as the
       bottom edge of a pill. */
    border-radius: 6px 6px 0 0 !important;
    border: none !important;
    background: transparent !important;
    color: %(muted)s !important;
    letter-spacing: 0 !important;
    /* Declared transparent so the active state only changes its colour - a
       border would shift every tab by 2px when you navigate. */
    box-shadow: inset 0 -2px 0 transparent !important;
    transition: none !important;
}
/* Label and icon follow the link's own colour, so idle / hover / active are
   set in one place. Without this the label keeps Streamlit's default ink and
   only the icon dims. */
[data-testid="stTopNavLink"] p, .stTopNavLink p,
[data-testid="stTopNavLink"] span, .stTopNavLink span {
    color: inherit !important;
    font-size: 0.95rem !important;
    font-weight: 500 !important;
    margin: 0 !important;
}
[data-testid="stTopNavLink"]:hover, .stTopNavLink:hover {
    background: %(tint_soft)s !important;
    color: %(periwinkle)s !important;
}

/* The page you are on. Streamlit sets aria-current itself. */
[aria-current="page"] [data-testid="stTopNavLink"],
[data-testid="stTopNavLink"][aria-current="page"],
a[aria-current="page"] {
    background: %(tint_soft)s !important;
    color: %(periwinkle)s !important;
    box-shadow: inset 0 -2px 0 %(periwinkle)s !important;
}

/* --- Cards ---------------------------------------------------------------
   A bordered container is transparent by default, so on the near-white canvas
   every card sits at the same value as the page. White plus a hairline shadow
   lifts them, and matches the sidebar, which is white for the same reason.

   Keyed rather than selected by test id: Streamlit 1.63 puts the border
   straight on [data-testid="stVerticalBlock"], with nothing to distinguish a
   bordered block from a plain one except an emotion hash that changes between
   releases. Every card that wants the surface is given a `card-*` key in
   steps.py, which is a documented, stable hook. */
[class*="st-key-card-"] {
    background: %(surface)s !important;
    box-shadow: 0 1px 2px rgba(44, 62, 80, .04);
}
%(callouts)s
/* --- Step marker ---------------------------------------------------------
   A belt-and-braces "where am I", independent of the nav styling above. */
.st-key-eyebrow p {
    color: %(muted)s !important;
    font-weight: 500 !important;
    font-size: 0.85rem !important;
}
%(libraries)s
</style>
""" % {
    "periwinkle": PERIWINKLE, "tint_soft": TINT_SOFT, "surface": SURFACE,
    "muted": MUTED, "callouts": CALLOUT_RULES, "libraries": LIBRARY_RULES,
}


def header_label(text):
    """Name the workshop beside the Ersilia wordmark, in place of a sidebar.

    Written with CSS rather than a widget because the header is Streamlit's own
    chrome and takes no content from the script. The wordmark is an <img>, and a
    replaced element cannot carry ::after, so the text hangs off its container.
    """
    return """<style>
/* The label hangs off the logo's own anchor, so it would otherwise pick up the
   link underline. */
[data-testid="stLogoLink"] { text-decoration: none !important; }
[data-testid="stHeader"] [data-testid="stLogoLink"]::after,
[data-testid="stHeader"] [data-testid="stLogoSpacer"]::after {
    content: %(text)s;
    margin-left: 0.85rem;
    padding-left: 0.85rem;
    border-left: 1px solid %(edge)s;
    color: %(muted)s;
    font-size: 0.9rem;
    font-weight: 500;
    white-space: nowrap;
    text-decoration: none;
    cursor: default;
}
[data-testid="stHeader"] [data-testid="stLogoLink"] {
    display: inline-flex !important;
    align-items: center;
}
</style>""" % {"text": _css_string(text), "edge": EDGE, "muted": MUTED}


def locked_tabs(url_paths):
    """Grey out the steps not yet reached, and stop them being clicked.

    Every step is always in the navigation so the shape of the workshop is
    visible from the start; this is what makes the unreached ones look and
    behave locked. render() in app.py refuses to draw their body as well, since
    pointer-events does not stop a typed URL or a keyboard activation.
    """
    if not url_paths:
        return "<style></style>"
    rules = "".join("""
a[href$="/%(path)s"] {
    pointer-events: none !important;
    opacity: 0.38 !important;
    cursor: not-allowed !important;
}
""" % {"path": p} for p in url_paths)
    return "<style>%s</style>" % rules
