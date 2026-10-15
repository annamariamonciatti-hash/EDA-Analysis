# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 12:45:41 2026

@author: Utente
"""

import glob
import os
import re

import pandas as pd
from scipy.stats import spearmanr

from config_eda_allsub import PIPELINE_VERSION


FEATURES = [
    "EDA_Tonic_Median",
    "EDA_Tonic_Mean",
    "EDA_Phasic_Max",
    "EDA_Phasic_STD",
    "SCR_Rate",
    "EDA_SympatheticN"
]

ALL_CONDITIONS = [
    "baseline",
    "SOM_CTR",
    "cognitive",
    "stress",
    "SOM_STR"
]


def subject_number(path):

    match = re.search(r"S(\d+)", path)

    return (
        int(match.group(1))
        if match
        else float("inf")
    )


def run_concatenate_and_check(database_dir):

    group_dir = os.path.join(
        database_dir,
        "Subjects_EDA"
    )

    os.makedirs(group_dir, exist_ok=True)

    pattern = os.path.join(
        database_dir,
        "S*",
        "csvs_merged",
        "processed_eda",
        f"eda_features_S*{PIPELINE_VERSION}.csv"
    )

    files = sorted(
        glob.glob(pattern),
        key=subject_number
    )

    print(
        f"Found {len(files)} "
        f"{PIPELINE_VERSION} feature files"
    )

    if not files:
        raise FileNotFoundError(
            f"No feature files found:\n{pattern}"
        )

    combined_df = pd.concat(
        [pd.read_csv(file) for file in files],
        ignore_index=True
    )

    group_path = os.path.join(
        group_dir,
        f"all_subjects_eda_{PIPELINE_VERSION}.csv"
    )

    combined_df.to_csv(
        group_path,
        index=False
    )

    print(f"✔ Saved: {group_path}")
    print(f"Rows: {len(combined_df)}")

    # Only analyse conditions actually present
    check_conditions = [
        condition
        for condition in ALL_CONDITIONS
        if condition in combined_df["condition"].unique()
    ]

    print(
        f"Conditions included in duration sensitivity check: "
        f"{check_conditions}"
    )

    results = []

    for condition in check_conditions:

        temp = combined_df[
            combined_df["condition"] == condition
        ]

        for feature in FEATURES:

            temp2 = temp[
                ["duration_sec", feature]
            ].dropna()

            if len(temp2) < 5:
                print(
                    f"{condition} - {feature}: "
                    "insufficient data"
                )
                continue

            rho, p = spearmanr(
                temp2["duration_sec"],
                temp2[feature]
            )

            results.append({
                "Condition": condition,
                "Feature": feature,
                "Spearman_rho": rho,
                "p_value": p,
                "N": len(temp2)
            })

    results_df = pd.DataFrame(results)

    check_path = os.path.join(
        group_dir,
        f"duration_sensitivity{PIPELINE_VERSION}.csv"
    )

    results_df.to_csv(
        check_path,
        index=False
    )


    print(f"✔ Saved: {check_path}")

    return group_path