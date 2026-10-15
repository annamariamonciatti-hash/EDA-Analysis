# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 12:48:51 2026

@author: Utente
"""

import os

import matplotlib.pyplot as plt
import pandas as pd

from config_eda_allsub import PIPELINE_VERSION


COLS = [
    "EDA_Tonic_Mean",
    "EDA_SympatheticN",
    "EDA_Phasic_Max",
    "EDA_Phasic_STD",
    "SCR_Rate",
]

ALL_CONDITIONS = [
    "baseline",
    "SOM_CTR",
    "cognitive",
    "stress",
    "SOM_STR"
]


def run_plots(data_path, sig_path):

    df = pd.read_csv(data_path, sep=",")
    df.columns = df.columns.str.strip()

    df = df.dropna(
        subset=["condition", "subject"]
    )

    df["condition"] = df["condition"].astype(str)
    df = df.dropna(how="all")

    # Conditions actually present in the dataset
    conditions = [
        c for c in ALL_CONDITIONS
        if c in df["condition"].unique()
    ]

    sig_df = pd.DataFrame(
        columns=["feature", "cond1", "cond2", "sig"]
    )

    try:
        sig_df = pd.read_csv(sig_path)
        sig_df.columns = sig_df.columns.str.strip()

    except (
        pd.errors.EmptyDataError,
        FileNotFoundError
    ):

        print(
            "\nWARNING: Wilcoxon results file is empty "
            "or not found."
        )

        print(
            "Plots will be generated without "
            "significance annotations."
        )

    cols = [
        col for col in COLS
        if col in df.columns
    ]

    for col in cols:

        df[col] = pd.to_numeric(
            df[col]
            .astype(str)
            .str.replace(",", "."),
            errors="coerce"
        )

    df["condition"] = pd.Categorical(
        df["condition"],
        categories=conditions,
        ordered=True
    )

    out_dir = os.path.join(
        os.path.dirname(data_path),
        "plots",
        PIPELINE_VERSION
    )

    os.makedirs(
        out_dir,
        exist_ok=True
    )

    # Dynamic positions
    positions = [
        1 + i * 1.5
        for i in range(len(conditions))
    ]

    condition_positions = dict(
        zip(conditions, positions)
    )

    for feat in cols:

        print(f"✔ Plotting {feat}")

        y_label = (
            "n.u."
            if "sympatheticn" in feat.lower()
            else "μS"
        )

        data_raw = [
            df[
                df["condition"] == cond
            ][feat].dropna().values
            for cond in conditions
        ]

        # =====================================================
        # LINE PLOT
        # =====================================================

        plt.figure(figsize=(9, 5))

        for subject in df["subject"].unique():

            sub = df[
                df["subject"] == subject
            ].sort_values("condition")

            sub = sub.dropna(
                subset=[feat, "condition"]
            )

            x_values = [
                condition_positions[c]
                for c in sub["condition"]
            ]

            y_values = sub[feat]

            plt.plot(
                x_values,
                y_values,
                marker="o",
                alpha=0.8,
                label=f"Soggetto {subject}"
            )

        plt.xticks(
            positions,
            conditions,
            rotation=20,
            ha="right"
        )

        plt.title(feat)
        plt.ylabel(y_label)

        plt.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=8
        )

        plt.tight_layout()

        plt.savefig(
            os.path.join(
                out_dir,
                f"{feat}_line_{PIPELINE_VERSION}.png"
            ),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

        # =====================================================
        # BOXPLOT
        # =====================================================

        fig, ax = plt.subplots(
            figsize=(11, 5)
        )

        ax.boxplot(
            data_raw,
            positions=positions,
            widths=0.7
        )

        ax.set_xticks(positions)

        ax.set_xticklabels(
            conditions,
            rotation=20,
            ha="right"
        )

        ax.set_title(feat)
        ax.set_ylabel(y_label)

        feat_sig = sig_df[
            sig_df["feature"] == feat
        ].copy()

        significance_lines = []

        for _, row in feat_sig.iterrows():

            significance_lines.append(
                f"{row['cond1']} – "
                f"{row['cond2']}: "
                f"{row['sig']}"
            )

        significance_text = "\n".join(
            significance_lines
        )

        if significance_text:

            ax.text(
                1.03,
                0.98,
                significance_text,
                transform=ax.transAxes,
                fontsize=9,
                verticalalignment="top",
                horizontalalignment="left"
            )

        plt.tight_layout()

        plt.savefig(
            os.path.join(
                out_dir,
                f"{feat}_box_{PIPELINE_VERSION}.png"
            ),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

        # =====================================================
        # VIOLIN PLOT
        # =====================================================

        fig, ax = plt.subplots(
            figsize=(9, 5)
        )

        ax.violinplot(
            data_raw,
            positions=positions,
            widths=0.9
        )

        ax.set_xticks(positions)

        ax.set_xticklabels(
            conditions,
            rotation=20,
            ha="right"
        )

        ax.set_title(feat)
        ax.set_ylabel(y_label)

        plt.tight_layout()

        plt.savefig(
            os.path.join(
                out_dir,
                f"{feat}_violin_{PIPELINE_VERSION}.png"
            ),
            dpi=300,
            bbox_inches="tight"
        )

        plt.close()

    print(
        f"\n🚀 Plots saved in: {out_dir}"
    )

    return out_dir