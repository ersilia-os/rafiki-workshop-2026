"""Molecule drawing, done in the browser with RDKit.js.

The server has no rdkit. Streamlit Community Cloud's Python 3.14 image does not
carry libXrender.so.1, which rdkit's wheel needs at import time, and packages.txt
cannot supply it: the image has a stale bullseye-security apt source whose
Release file expired on 2026-09-07, so apt-get exits non-zero and Cloud aborts
the build before pip runs. Both confirmed against the build log.

RDKit.js is the same C++ code compiled to WebAssembly, so these are the drawings
rdkit would have produced, and the server needs no rdkit at all.

Two things to know before editing the JavaScript below.

1. st.html is NOT iframed, so every molecule on a page shares one window.RDKit
   and the WebAssembly is instantiated once.
2. Streamlit sanitises the HTML with DOMPurify, and DOMPurify discards the whole
   <script> element if its source text contains literal HTML markup with
   attributes - a plain `el.innerHTML = '<div style="...">'` silently removes
   the script and nothing runs. So build nodes with createElement and set style
   properties. Assigning a *variable* to innerHTML is fine: that happens in the
   browser, long after sanitisation.
"""

import json
import uuid

import streamlit as st

# Served from static/ by [server] enableStaticServing in config.toml, so there
# is no CDN dependency at runtime. Refresh both files together, from the same
# @rdkit/rdkit release.
RDKIT_JS = "/app/static/RDKit_minimal.js"
RDKIT_WASM = "/app/static/RDKit_minimal.wasm"

HIGHLIGHT = [0.902, 0.216, 0.271]        # #e63745, the attachment-point marker
BORDER = "#E6E6EE"
MUTED = "#6B6675"

# Idempotent and emitted with every block: the promise is memoised on window, so
# the WebAssembly is fetched and instantiated once however often this appears.
_LOADER = """
window.__molFail = window.__molFail || function (el, msg) {
  var d = document.createElement('div');
  d.style.color = %(muted)s;
  d.style.fontSize = '12px';
  d.style.padding = '8px';
  d.textContent = msg;
  el.replaceChildren(d);
};
window.__rdkit = window.__rdkit || new Promise(function (resolve, reject) {
  if (window.RDKit) { resolve(window.RDKit); return; }
  var s = document.createElement('script');
  s.src = window.location.origin + %(js)s;
  s.onload = function () {
    initRDKitModule({locateFile: function () {
      return window.location.origin + %(wasm)s;
    }}).then(function (m) { window.RDKit = m; resolve(m); }, reject);
  };
  s.onerror = function () { reject(new Error('could not load RDKit.js')); };
  document.head.appendChild(s);
});
""" % {"js": json.dumps(RDKIT_JS), "wasm": json.dumps(RDKIT_WASM),
       "muted": json.dumps(MUTED)}


def draw_molecule(smiles, size=(200, 200), highlight_dummies=True):
    """One molecule. Any attachment point is picked out, since a bare `*` is
    easy to miss and it is the whole point of a scaffold."""
    target = "mol-" + uuid.uuid4().hex
    width, height = size
    st.html(
        """<div id="%(id)s" style="width:%(w)dpx;height:%(h)dpx"></div>
<script>
%(loader)s
window.__rdkit.then(function (RDKit) {
  var el = document.getElementById(%(id_json)s);
  if (!el) { return; }
  var mol = RDKit.get_mol(%(smiles)s);
  if (!mol || !mol.is_valid()) {
    if (mol) { mol.delete(); }
    window.__molFail(el, 'Could not read this structure.');
    return;
  }
  try {
    var atoms = [];
    if (%(highlight)s) {
      var q = RDKit.get_qmol('[#0]');
      // get_substruct_matches returns {} rather than [] when nothing matches,
      // so this has to be checked: .forEach on it throws, and a throw in here
      // would leave an empty box with no message.
      var found = JSON.parse(mol.get_substruct_matches(q));
      if (Array.isArray(found)) {
        found.forEach(function (m) { atoms = atoms.concat(m.atoms); });
      }
      q.delete();
    }
    el.innerHTML = atoms.length
      ? mol.get_svg_with_highlights(JSON.stringify(
          {atoms: atoms, highlightColour: %(colour)s, width: %(w)d, height: %(h)d}))
      : mol.get_svg(%(w)d, %(h)d);
  } catch (e) {
    window.__molFail(el, 'Structure drawing unavailable.');
  }
  mol.delete();
}, function () {
  var el = document.getElementById(%(id_json)s);
  if (el) { window.__molFail(el, 'Structure drawing unavailable.'); }
});
</script>""" % {
            "id": target, "id_json": json.dumps(target),
            "w": width, "h": height,
            "loader": _LOADER,
            "smiles": json.dumps(smiles),
            "highlight": "true" if highlight_dummies else "false",
            "colour": json.dumps(HIGHLIGHT),
        },
        unsafe_allow_javascript=True,
    )


def draw_molecules_grid(smiles_list, legends, per_row=4, size=(260, 220)):
    """A grid of molecules with a caption under each, replacing rdkit's
    MolsToGridImage. The layout is CSS rather than baked into one bitmap, so it
    reflows with the column and the structures stay sharp on a projector."""
    target = "grid-" + uuid.uuid4().hex
    width, height = size
    st.html(
        """<div id="%(id)s" style="display:grid;
     grid-template-columns:repeat(%(per_row)d, minmax(0, 1fr));gap:6px;width:100%%"></div>
<script>
%(loader)s
window.__rdkit.then(function (RDKit) {
  var el = document.getElementById(%(id_json)s);
  if (!el) { return; }
  var smiles = %(smiles)s, legends = %(legends)s;
  var frag = document.createDocumentFragment();
  try {
  for (var i = 0; i < smiles.length; i++) {
    var fig = document.createElement('figure');
    fig.style.margin = '0';
    fig.style.border = '1px solid ' + %(border)s;
    fig.style.borderRadius = '8px';
    fig.style.background = '#FFFFFF';
    fig.style.padding = '4px';
    var box = document.createElement('div');
    box.style.display = 'flex';
    box.style.justifyContent = 'center';
    var mol = RDKit.get_mol(smiles[i]);
    if (mol && mol.is_valid()) { box.innerHTML = mol.get_svg(%(w)d, %(h)d); }
    if (mol) { mol.delete(); }
    var cap = document.createElement('figcaption');
    cap.style.fontSize = '11px';
    cap.style.color = %(muted)s;
    cap.style.textAlign = 'center';
    cap.style.padding = '2px 0 4px';
    cap.textContent = legends[i] || '';
    fig.appendChild(box);
    fig.appendChild(cap);
    frag.appendChild(fig);
  }
  el.replaceChildren(frag);
  } catch (e) {
    window.__molFail(el, 'Structure drawing unavailable.');
  }
}, function () {
  var el = document.getElementById(%(id_json)s);
  if (el) { window.__molFail(el, 'Structure drawing unavailable.'); }
});
</script>""" % {
            "id": target, "id_json": json.dumps(target),
            "per_row": per_row, "w": width, "h": height,
            "loader": _LOADER,
            "smiles": json.dumps(list(smiles_list)),
            "legends": json.dumps([str(x) for x in legends]),
            "border": json.dumps(BORDER), "muted": json.dumps(MUTED),
        },
        unsafe_allow_javascript=True,
    )
