# Rafiki Workshop 2026

Streamlit app for the Rafiki 2026 workshop, developed by the [Ersilia Open Source Initiative](https://ersilia.io).
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
python scripts/01_prepare_saureus_dataset.py   # needs the eu-openscreen repo alongside this one
bash   scripts/02_run_featurisers.sh           # ersilia: eos4wt0, eos9o72, eos1klk (~20 min)
                                               # raw output lands in data/raw/, not versioned
python scripts/03_pack_descriptors.py
python scripts/05_make_favicon.py             # the plum page icon
```

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

`requirements.txt` is the only dependency file, and there is deliberately no
`packages.txt` - see the comments in it before adding one.

Set `RAFIKI_UNLOCK_ALL=1` to reach every step without walking the workshop in order.

`app/info.py` is the only file to edit to change the dataset, the descriptors, the models or the
workshop text.

## License

Code is released under a [GPLv3](LICENSE) license. Workshop materials are released under a CC-BY-4 license.

## Contact

[hello@ersilia.io](mailto:hello@ersilia.io)
