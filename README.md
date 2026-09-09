# RAFIKI Workshop 2026

Streamlit app for the RAFIKI 2026 workshop, developed by the [Ersilia Open Source Initiative](https://ersilia.io).

Participants inspect a *Staphylococcus aureus* screen, choose an activity cut-off, train a classifier
on two molecular representations, screen a new compound library, and finish by expanding the one
natural product that sits in every group's library.

The activity data comes from the EU-OPENSCREEN ECBD assay "MSSA ATCC 29213 Anti-Bacterial Assay"
(*S. aureus* ATCC 29213, 50 uM single point), via
[eu-openscreen-antimicrobial-tasks](https://github.com/ersilia-os/eu-openscreen-antimicrobial-tasks).

- [Workshop documentation](https://ersilia.gitbook.io/ersilia-workshops/rafiki)
- [Workshop app](https://rafiki.streamlit.app)

## Run the app locally

```bash
pip install -r requirements.txt
streamlit run app/app.py
```

## Reproduce the precalculations

```bash
pip install -r scripts/requirements.txt  
python scripts/01_prepare_saureus_dataset.py
bash   scripts/02_run_featurisers.sh 
# ... etcetera
```

## License

Code is released under a [GPLv3](LICENSE) license. Workshop materials are released under a CC-BY-4 license.

## About the Ersilia Open Source Initiative

[Ersilia](https://ersilia.io) is a not for profit organisation supporting AI/ML adoption in the Global South, especially in Africa. This workshop is part of Ersilia's capacity strengthening activities.
