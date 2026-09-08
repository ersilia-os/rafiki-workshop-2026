# RAFIKI Workshop 2026

Streamlit app for the RAFIKI 2026 workshop, developed by the [Ersilia Open Source Initiative](https://ersilia.io).
Participants inspect a *Staphylococcus aureus* screen, choose an activity cut-off, train a classifier
on two molecular representations, screen a new compound library, and finish by expanding the one
natural product that sits in every group's library.

The activity data comes from the EU-OPENSCREEN ECBD assay "MSSA ATCC 29213 Anti-Bacterial Assay"
(*S. aureus* ATCC 29213, 50 uM single point), via
[eu-openscreen-antimicrobial-tasks](https://github.com/ersilia-os/eu-openscreen-antimicrobial-tasks).

## Data

`data/` ships with the repository (~23 MB). Descriptor matrices are compressed `.npz`:
binary fingerprints as `uint8`, embeddings as `float16`. To rebuild from scratch:

```bash
pip install -r scripts/requirements.txt        # not the app's requirements.txt
python scripts/01_prepare_saureus_dataset.py   # needs the eu-openscreen repo alongside this one
bash   scripts/02_run_featurisers.sh           # ersilia: eos4wt0, eos9o72, eos1klk (~20 min)
                                               # raw output lands in data/raw/, not versioned
python scripts/03_pack_descriptors.py
python scripts/04_assign_rafiki_ids.py         # RAFIKI-0001.. for every library compound
python scripts/05_make_favicon.py              # the plum page icon
```

`data/rafiki_ids.csv` gives each of the 5,995 compounds across the six libraries a stable
identifier. It is committed rather than generated at runtime, so a participant's
`RAFIKI-0421` means the same compound in every session. The union is 5,995 and not 6,000
because platensimycin is in all six libraries - as its flat form, with no stereochemistry,
so it does not match `PARENT_SMILES` as a string.

`data/analogues_master.csv` (1,062 platensimycin analogues from five generative models, already
scored) comes from a separate analysis and is not rebuilt by these scripts. Column meanings are
documented in that analysis, not here; `app/info.py` names the four columns the app actually uses.

To see the app working without waiting for the featurisers,
`python scripts/99_placeholder_descriptors.py` writes random stand-ins and the app shows a warning
banner while they are in place.

## Run

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

`requirements.txt` is the app's runtime and the only file Community Cloud installs.
What the data-preparation scripts need is kept separately in
`scripts/requirements.txt`, which Cloud never reads.

There is no `packages.txt`, and no rdkit in the app. Molecules are drawn in the browser
by RDKit.js - the same C++ code compiled to WebAssembly - wired up in `app/molecules.py`.
The rdkit wheel needs `libXrender.so.1` at import time, Community Cloud's Python 3.14
image does not carry it, and a `packages.txt` cannot supply it either: the image has a
stale bullseye-security apt source whose Release file expired on 2026-09-07, so `apt-get`
exits non-zero and Cloud aborts the build before pip runs. Both confirmed against the
build log. Drawing client-side removes the dependency instead of working around it, and
rdkit was used nowhere else in `app/`.

RDKit.js is served from `app/static/` via `enableStaticServing`, not from a CDN, so a room
of participants does not each fetch 7 MB from jsdelivr at once. Refresh
`RDKit_minimal.js` and `RDKit_minimal.wasm` together, from one `@rdkit/rdkit` release.

Set `RAFIKI_UNLOCK_ALL=1` to reach every step without walking the workshop in order.

`app/info.py` is the only file to edit to change the dataset, the descriptors, the models or the
workshop text.

## License

Code is released under a [GPLv3](LICENSE) license. Workshop materials are released under a CC-BY-4 license.

## Contact

[hello@ersilia.io](mailto:hello@ersilia.io)
