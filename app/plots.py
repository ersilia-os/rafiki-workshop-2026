import altair as alt
import numpy as np
import pandas as pd

# The chemical space scatter carries one row per compound, past Altair's
# default 5000-row embed cap. Vega renders it to canvas and copes fine.
alt.data_transformers.disable_max_rows()


def _framed(chart):
    """stylia's habit: keep the full frame, lay a light grid behind the data."""
    return chart.configure_view(stroke=GRID, strokeWidth=1).configure_axis(
        gridColor=GRID, gridOpacity=0.45, tickCount=5, domainColor=GRID, tickColor=GRID,
        labelColor="#6B6675", titleColor="#6B6675", labelFontSize=11, titleFontSize=11,
    )

# Ersilia house chart set: brand hues snapped for legibility. Red is reserved
# for slot 6 and deliberately not used for "active" - an active compound is a
# good outcome. Plum is the identity accent, used only for reference markers.
PRIMARY = "#6d5de7"
ACTIVE = PRIMARY   # the interesting class takes slot 1, never the red slot
NEUTRAL = "#C7C4D4"
PLUM = "#50285A"
GRID = "#DDDDDD"

# A log axis has no zero, so bar marks collapse to a line at their own value.
# Square root keeps a true zero baseline - so the bars are real columns - while
# still compressing the noise peak enough to see the tail. "linear" also works.
HISTOGRAM_COUNT_SCALE = "sqrt"


def plot_readout_histogram(df, readout_column, cutoff, label, bins=45):
    """Histogram of the readout. Bins on the active side of the cut-off are red."""
    values = df[readout_column].dropna()
    counts, edges = np.histogram(values, bins=bins)
    active_counts, _ = np.histogram(values[df["Binary"] == 1], bins=edges)

    hist = pd.DataFrame({
        "start": edges[:-1], "end": edges[1:], "Compounds": counts,
        "Active": active_counts > counts / 2,
    })
    hist = hist[hist["Compounds"] > 0]

    bars = (
        alt.Chart(hist)
        .mark_bar()
        .encode(
            # bin="binned" tells Vega the data is already binned. Without it,
            # x plus x2 is a ranged mark and every bar renders as a flat dash.
            x=alt.X("start:Q", bin="binned", title=label,
                    axis=alt.Axis(tickCount=6, grid=False)),
            x2="end:Q",
            y=alt.Y(
                "Compounds:Q",
                scale=alt.Scale(type=HISTOGRAM_COUNT_SCALE),
                axis=alt.Axis(tickCount=4),
            ),
            color=alt.Color(
                "Active:N",
                scale=alt.Scale(domain=[False, True], range=[NEUTRAL, ACTIVE]),
                legend=None,
            ),
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"cutoff": [cutoff]}))
        .mark_rule(color=PLUM, size=2, strokeDash=[4, 3])
        .encode(x=alt.X("cutoff:Q", title=label))
    )
    return _framed((bars + rule).properties(height=380))


def plot_fold_scores(y_true, y_pred):
    """One cross-validation fold: where the model actually put each class.

    A box per class with the individual test compounds jittered over it, so the
    overlap between actives and inactives is visible rather than summarised.
    """
    df = pd.DataFrame({
        "Class": ["Active" if v == 1 else "Inactive" for v in y_true],
        "Score": list(y_pred),
    })
    colour = alt.Color(
        "Class:N",
        scale=alt.Scale(domain=["Inactive", "Active"], range=[NEUTRAL, ACTIVE]),
        legend=None,
    )
    base = alt.Chart(df).encode(
        x=alt.X("Class:N", title=None, sort=["Inactive", "Active"],
                axis=alt.Axis(labelAngle=0)),
        y=alt.Y("Score:Q", title="Predicted probability"),
    )
    points = (
        base.transform_calculate(jitter="sqrt(-2*log(random()))*cos(2*PI*random())")
        .mark_circle(size=10, opacity=0.25)
        .encode(xOffset=alt.XOffset("jitter:Q", scale=alt.Scale(domain=[-3, 3])), color=colour)
    )
    box = base.mark_boxplot(size=34, outliers=False, opacity=0.55).encode(color=colour)
    return _framed((points + box).properties(height=240))


def plot_score_distribution(values, label, marker=None, bins=40):
    """Distribution of a predicted score, with an optional threshold marker."""
    counts, edges = np.histogram(values.dropna(), bins=bins)
    hist = pd.DataFrame({"start": edges[:-1], "end": edges[1:], "Compounds": counts})
    hist = hist[hist["Compounds"] > 0]
    bars = (
        alt.Chart(hist)
        .mark_bar(color=NEUTRAL)
        .encode(
            x=alt.X("start:Q", bin="binned", title=label,
                    axis=alt.Axis(tickCount=6, grid=False)),
            x2="end:Q",
            y=alt.Y("Compounds:Q", axis=alt.Axis(tickCount=4)),
        )
    )
    if marker is None:
        return _framed(bars.properties(height=260))
    rule = (
        alt.Chart(pd.DataFrame({"x": [marker]}))
        .mark_rule(color=PLUM, size=2, strokeDash=[4, 3])
        .encode(x=alt.X("x:Q", title=label))
    )
    return _framed((bars + rule).properties(height=260))


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
                scale=alt.Scale(domain=[0, 1], range=[NEUTRAL, ACTIVE]),
                legend=alt.Legend(
                    title=None,
                    labelExpr="if(datum.label == '1', 'Active', 'Inactive')",
                    orient="bottom",
                ),
            ),
        )
        .properties(height=380)
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
    return _framed((points + vline + hline + parent).properties(height=430))
