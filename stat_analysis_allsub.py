
# -*- coding: utf-8 -*-

from itertools import combinations

import numpy as np
import pandas as pd

from scipy.stats import (
    friedmanchisquare,
    rankdata,
    ttest_rel,
    wilcoxon
)

from statsmodels.stats.anova import AnovaRM
from statsmodels.stats.multitest import multipletests


ALL_CONDITIONS = [
    "baseline",
    "SOM_CTR",
    "cognitive",
    "stress",
    "SOM_STR"
]

FDR_METHOD = "fdr_tsbky"
FDR_ALPHA = 0.05


def stars(p):
    if not np.isfinite(p):
        return "ns"
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else "ns"


def get_conditions(df):
    """Restituisce solo le condizioni presenti, nell'ordine sperimentale."""
    if "condition" not in df.columns:
        return []

    present = set(df["condition"].dropna().astype(str).str.strip())
    return [c for c in ALL_CONDITIONS if c in present]


def apply_fdr(results, pvals):
    if not results:
        return pd.DataFrame()

    corrected = multipletests(
        pvals,
        alpha=FDR_ALPHA,
        method=FDR_METHOD
    )[1]

    for result, p in zip(results, corrected):
        result["p_value"] = p
        result["sig"] = stars(p)

    return pd.DataFrame(results)


def rank_biserial(x, y):
    diff = np.asarray(y) - np.asarray(x)
    diff = diff[diff != 0]

    if len(diff) == 0:
        return np.nan

    ranks = rankdata(np.abs(diff))
    pos = ranks[diff > 0].sum()
    neg = ranks[diff < 0].sum()

    return (pos - neg) / (pos + neg)


def _complete_pivot(df, feature, conditions):
    """Restituisce i soggetti con dati validi in tutte le condizioni."""
    sub = df[df["condition"].isin(conditions)].copy()
    sub[feature] = pd.to_numeric(sub[feature], errors="coerce")

    pivot = sub.pivot(
        index="subject",
        columns="condition",
        values=feature
    )

    return pivot.reindex(columns=conditions).dropna()


def run_analysis_friedman(df, features):
    conditions = get_conditions(df)

    columns = [
        "feature", "chi2", "df", "kendalls_w",
        "p_raw", "p_value", "sig"
    ]

    if len(conditions) < 2:
        return pd.DataFrame(columns=columns)

    results, pvals = [], []

    for feature in features:
        pivot = _complete_pivot(df, feature, conditions)

        if len(pivot) < 3:
            continue

        # Friedman non è informativo se tutti i soggetti hanno
        # valori identici in tutte le condizioni.
        if (pivot.nunique(axis=1) == 1).all():
            continue

        try:
            chi2, p = friedmanchisquare(
                *[pivot[c].to_numpy() for c in conditions]
            )
        except (ValueError, ZeroDivisionError):
            continue

        if not np.isfinite(p):
            continue

        n = len(pivot)
        k = len(conditions)

        results.append({
            "feature": feature,
            "chi2": chi2,
            "df": k - 1,
            "kendalls_w": chi2 / (n * (k - 1)),
            "p_raw": p
        })
        pvals.append(p)

    result_df = apply_fdr(results, pvals)
    return result_df if not result_df.empty else pd.DataFrame(columns=columns)


def run_analysis_anova(df, features):
    conditions = get_conditions(df)

    columns = [
        "feature", "F", "df1", "df2",
        "p_raw", "p_value", "sig"
    ]

    if len(conditions) < 2:
        return pd.DataFrame(columns=columns)

    results, pvals = [], []

    for feature in features:
        pivot = _complete_pivot(df, feature, conditions)

        if len(pivot) < 3:
            continue

        sub = pivot.reset_index().melt(
            id_vars="subject",
            value_vars=conditions,
            var_name="condition",
            value_name="value"
        )

        try:
            tab = AnovaRM(
                sub,
                depvar="value",
                subject="subject",
                within=["condition"]
            ).fit().anova_table
        except (ValueError, ZeroDivisionError):
            continue

        p = tab["Pr > F"].iloc[0]

        if not np.isfinite(p):
            continue

        results.append({
            "feature": feature,
            "F": tab["F Value"].iloc[0],
            "df1": tab["Num DF"].iloc[0],
            "df2": tab["Den DF"].iloc[0],
            "p_raw": p
        })
        pvals.append(p)

    result_df = apply_fdr(results, pvals)
    return result_df if not result_df.empty else pd.DataFrame(columns=columns)


def run_posthoc_wilcoxon(df, stats_df):
    columns = [
        "feature", "cond1", "cond2",
        "median_cond1", "median_cond2", "median_difference",
        "W", "effect_size_r", "p_raw", "p_value", "sig"
    ]

    conditions = get_conditions(df)

    if len(conditions) < 2 or stats_df.empty:
        return pd.DataFrame(columns=columns)

    features = stats_df.loc[
        stats_df["p_value"] < .05, "feature"
    ]

    frames = []

    for feature in features:
        pivot = df[df["condition"].isin(conditions)].pivot(
            index="subject",
            columns="condition",
            values=feature
        )

        results, pvals = [], []

        for c1, c2 in combinations(conditions, 2):
            if c1 not in pivot.columns or c2 not in pivot.columns:
                continue

            paired = pivot[[c1, c2]].dropna()

            if len(paired) < 3:
                continue

            x, y = paired[c1].to_numpy(), paired[c2].to_numpy()

            try:
                W, p = wilcoxon(x, y)
            except ValueError:
                W, p = np.nan, 1.0

            results.append({
                "feature": feature,
                "cond1": c1,
                "cond2": c2,
                "median_cond1": np.median(x),
                "median_cond2": np.median(y),
                "median_difference": np.median(y) - np.median(x),
                "W": W,
                "effect_size_r": rank_biserial(x, y),
                "p_raw": p
            })
            pvals.append(p)

        frame = apply_fdr(results, pvals)
        if not frame.empty:
            frames.append(frame)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)


def run_posthoc_pairedttest(df, stats_df):
    columns = [
        "feature", "cond1", "cond2",
        "mean_cond1", "mean_cond2", "mean_difference",
        "t", "df", "effect_size_dz", "p_raw", "p_value", "sig"
    ]

    conditions = get_conditions(df)

    if len(conditions) < 2 or stats_df.empty:
        return pd.DataFrame(columns=columns)

    features = stats_df.loc[
        stats_df["p_value"] < .05, "feature"
    ]

    frames = []

    for feature in features:
        pivot = df[df["condition"].isin(conditions)].pivot(
            index="subject",
            columns="condition",
            values=feature
        )

        results, pvals = [], []

        for c1, c2 in combinations(conditions, 2):
            if c1 not in pivot.columns or c2 not in pivot.columns:
                continue

            paired = pivot[[c1, c2]].dropna()

            if len(paired) < 3:
                continue

            x, y = paired[c1].to_numpy(), paired[c2].to_numpy()

            with np.errstate(divide="ignore", invalid="ignore"):
                t, p = ttest_rel(x, y)

            if not np.isfinite(p):
                continue

            n = len(x)

            results.append({
                "feature": feature,
                "cond1": c1,
                "cond2": c2,
                "mean_cond1": np.mean(x),
                "mean_cond2": np.mean(y),
                "mean_difference": np.mean(y) - np.mean(x),
                "t": t,
                "df": n - 1,
                "effect_size_dz": t / np.sqrt(n),
                "p_raw": p
            })
            pvals.append(p)

        frame = apply_fdr(results, pvals)
        if not frame.empty:
            frames.append(frame)

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=columns)
