import altair as alt
import numpy as np
import pandas as pd

# The chemical space scatter carries one row per compound, past Altair's
# default 5000-row embed cap. Vega renders it to canvas and copes fine.
alt.data_transformers.disable_max_rows()


def _framed(chart):
    """stylia's habit: keep the full frame, lay a light grid behind the data."""
    return chart.configure_view(stroke=GRID, strokeWidth=1).configure_axis(
        gridColor=GRID, gridOpacity=0.6, domainColor=GRID, tickColor=GRID,
        labelColor="#6B6675", titleColor="#6B6675", labelFontSize=11, titleFontSize=11,
    )

# Ersilia house chart set: brand hues snapped for legibility. Red is reserved
# for slot 6 and deliberately not used for "active" - an active compound is a
# good outcome. Plum is the identity accent, used only for reference markers.
PRIMARY = "#6d5de7"
NEUTRAL = "#C7C4D4"
PLUM = "#50285A"
GRID = "#DDDDDD"

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
        .mark_bar(color=PRIMARY)
        .encode(
            x=alt.X("start:Q", title=label),
            x2="end:Q",
            y=alt.Y("Compounds:Q", scale=alt.Scale(type=HISTOGRAM_COUNT_SCALE)),
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"cutoff": [cutoff]}))
        .mark_rule(color=PLUM, size=2)
        .encode(x=alt.X("cutoff:Q", title=label))
    )
    return _framed((bars + rule).properties(height=380))


def plot_chemical_space(projection, x_column, y_column, y):
    """Library projected onto Ersilia's reference chemical space, coloured by activity."""
    df = projection[[x_column, y_column]].copy()
    df["Binary"] = list(y)
    df = df.sort_values("Binary")  # actives drawn last, on top of the inactives
    chart = (
        alt.Chart(df)
        .mark_circle(size=18, opacity=0.6)
        .encode(
            x=alt.X("{0}:Q".format(x_column), title=None, axis=None),
            y=alt.Y("{0}:Q".format(y_column), title=None, axis=None),
            color=alt.Color(
                "Binary:N",
                scale=alt.Scale(domain=[0, 1], range=[NEUTRAL, PRIMARY]),
                legend=alt.Legend(
                    title=None,
                    labelExpr="if(datum.label == '1', 'Active', 'Inactive')",
                    orient="bottom",
                ),
            ),
        )
        .properties(height=380)
        .interactive()
    )
    return _framed(chart)


def plot_roc(tprs_df):
    """One muted curve per cross-validation fold, the mean picked out in colour."""
    folds = [c for c in tprs_df.columns if c.startswith("tpr_cv")]
    chart = (
        alt.Chart(tprs_df)
        .transform_fold(["Mean TPR"] + folds, as_=["Variable", "Value"])
        .mark_line()
        .encode(
            x=alt.X("FPR:Q", title="False positive rate"),
            y=alt.Y("Value:Q", title="True positive rate"),
            color=alt.Color(
                "Variable:N",
                scale=alt.Scale(range=[PRIMARY] + [NEUTRAL] * len(folds)),
                legend=None,
            ),
        )
        .properties(height=240)
    )
    return _framed(chart)


def plot_model_agreement(df, x_column, y_column, x_label, y_label):
    """One point per compound: do the two activity models rank it the same way?"""
    chart = (
        alt.Chart(df)
        .mark_circle(size=25, opacity=0.5, color=PRIMARY)
        .encode(
            x=alt.X("{0}:Q".format(x_column), title=x_label),
            y=alt.Y("{0}:Q".format(y_column), title=y_label),
            tooltip=[x_column, y_column],
        )
        .properties(height=380)
    )
    return _framed(chart)


def plot_pareto(df, x_column, y_column, shortlist_column, parent_x, parent_y, x_threshold):
    """Two objectives at once: keep the potency, gain the permeability.

    The parent sits at the crossing of the two dashed lines, so the shortlist is
    everything up and to the right of it.
    """
    points = (
        alt.Chart(df)
        .mark_circle(size=26, opacity=0.55)
        .encode(
            x=alt.X(x_column, scale=alt.Scale(zero=False), title="Predicted S. aureus activity"),
            y=alt.Y(y_column, scale=alt.Scale(zero=False), title="Predicted efflux evasion"),
            color=alt.Color(
                "{0}:N".format(shortlist_column),
                scale=alt.Scale(domain=[False, True], range=[NEUTRAL, PRIMARY]),
                legend=alt.Legend(
                    title=None, orient="bottom",
                    labelExpr="if(datum.label == 'true', 'Keeps potency, gains permeability', 'Everything else')",
                ),
            ),
            tooltip=["generator", x_column, y_column, "rdkit_mw"],
        )
    )
    rules = alt.Chart(pd.DataFrame({"x": [x_threshold], "y": [parent_y]}))
    vline = rules.mark_rule(strokeDash=[4, 4], color=PLUM).encode(x="x:Q")
    hline = rules.mark_rule(strokeDash=[4, 4], color=PLUM).encode(y="y:Q")
    parent = (
        alt.Chart(pd.DataFrame({"x": [parent_x], "y": [parent_y]}))
        .mark_point(size=260, shape="diamond", filled=True, color=PLUM, stroke="white", strokeWidth=1.5)
        .encode(x="x:Q", y="y:Q")
    )
    return _framed((points + vline + hline + parent).properties(height=430).interactive())
