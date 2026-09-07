import altair as alt
import numpy as np
import pandas as pd

# The chemical space scatter carries one row per compound, past Altair's
# default 5000-row embed cap. Vega renders it to canvas and copes fine.
alt.data_transformers.disable_max_rows()

ACTIVE = "#FF0000"
INACTIVE = "#0000FF"
BAR = "#1D6996"

# The actives are a fraction of a percent of the library, so on a linear count
# axis their bars are invisible next to the noise peak. Set to "linear" if you
# would rather not explain a log axis.
HISTOGRAM_COUNT_SCALE = "log"


def plot_readout_histogram(df, readout_column, cutoff, label, bins=50):
    """Distribution of the experimental readout, with the chosen cut-off marked.

    Binned in pandas rather than in Vega so the chart carries ~50 rows instead of
    the whole library, which also keeps it under Altair's 5000-row embed limit.
    """
    counts, edges = np.histogram(df[readout_column].dropna(), bins=bins)
    hist = pd.DataFrame({"start": edges[:-1], "end": edges[1:], "Compounds": counts})
    hist = hist[hist["Compounds"] > 0]
    bars = (
        alt.Chart(hist)
        .mark_bar(color=BAR)
        .encode(
            x=alt.X("start:Q", title=label),
            x2="end:Q",
            y=alt.Y("Compounds:Q", scale=alt.Scale(type=HISTOGRAM_COUNT_SCALE)),
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"cutoff": [cutoff]}))
        .mark_rule(color=ACTIVE, size=2)
        .encode(x=alt.X("cutoff:Q", title=label))
    )
    return (bars + rule).properties(title="Distribution of {0}".format(label.lower()))


def plot_chemical_space(projection, x_column, y_column, y):
    """Library projected onto Ersilia's reference chemical space, coloured by activity."""
    df = projection[[x_column, y_column]].copy()
    df["Binary"] = list(y)
    df = df.sort_values("Binary")  # actives drawn last, on top of the inactives
    return (
        alt.Chart(df)
        .mark_circle(size=18, opacity=0.6)
        .encode(
            x=alt.X("{0}:Q".format(x_column), title=None, axis=None),
            y=alt.Y("{0}:Q".format(y_column), title=None, axis=None),
            color=alt.Color(
                "Binary:N",
                scale=alt.Scale(domain=[0, 1], range=[INACTIVE, ACTIVE]),
                legend=alt.Legend(
                    title=None,
                    labelExpr="if(datum.label == '1', 'Active', 'Inactive')",
                    orient="bottom",
                ),
            ),
        )
        .properties(title="Chemical space", height=420)
        .configure_title(anchor="middle")
        .interactive()
    )


def plot_roc(tprs_df):
    """Grey curve per cross-validation fold, blue mean curve."""
    folds = [c for c in tprs_df.columns if c.startswith("tpr_cv")]
    return (
        alt.Chart(tprs_df)
        .transform_fold(["Mean TPR"] + folds, as_=["Variable", "Value"])
        .mark_line()
        .encode(
            x=alt.X("FPR:Q", title="False positive rate"),
            y=alt.Y("Value:Q", title="True positive rate"),
            color=alt.Color(
                "Variable:N",
                scale=alt.Scale(range=[INACTIVE] + ["#d3d3d3"] * len(folds)),
                legend=None,
            ),
        )
        .properties(title="ROC curve")
        .configure_title(anchor="middle")
        .interactive()
    )


def plot_model_agreement(df, x_column, y_column, x_label, y_label):
    """One point per compound: do the two activity models rank it the same way?"""
    return (
        alt.Chart(df)
        .mark_circle(size=25, opacity=0.5, color=BAR)
        .encode(
            x=alt.X("{0}:Q".format(x_column), title=x_label),
            y=alt.Y("{0}:Q".format(y_column), title=y_label),
            tooltip=[x_column, y_column],
        )
        .properties(title="Do the two models agree?")
        .configure_title(anchor="middle")
        .interactive()
    )
