# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 12:46:37 2026

@author: Utente
"""

# -*- coding: utf-8 -*-

import os
import pandas as pd

from config_eda_allsub import PIPELINE_VERSION

from stat_analysis_allsub import (
    run_analysis_anova,
    run_analysis_friedman,
    run_posthoc_pairedttest,
    run_posthoc_wilcoxon
)


def run_stats(group_path):

    base_dir = os.path.dirname(group_path)
    group_df = pd.read_csv(group_path)

    features = [
        col for col in group_df.columns
        if col not in [
            "subject",
            "condition",
            "duration_sec"
        ]
    ]

    print("\nFeatures analyzed:")

    for feature in features:
        print(f" - {feature}")

    friedman = run_analysis_friedman(
        group_df,
        features
    )

    wilcoxon = run_posthoc_wilcoxon(
        group_df,
        friedman
    )

    anova = run_analysis_anova(
        group_df,
        features
    )

    paired_ttest = run_posthoc_pairedttest(
        group_df,
        anova
    )

    outputs = {
        "friedman": os.path.join(
            base_dir,
            f"stats_results_eda_friedman{PIPELINE_VERSION}.csv"
        ),
        "wilcoxon": os.path.join(
            base_dir,
            f"posthoc_results_eda_wilkoxon{PIPELINE_VERSION}.csv"
        ),
        "anova": os.path.join(
            base_dir,
            f"stats_results_eda_anova{PIPELINE_VERSION}.csv"
        ),
        "pairedttest": os.path.join(
            base_dir,
            f"posthoc_results_eda_pairedttest{PIPELINE_VERSION}.csv"
        )
    }

    friedman.to_csv(outputs["friedman"], index=False)
    wilcoxon.to_csv(outputs["wilcoxon"], index=False)
    anova.to_csv(outputs["anova"], index=False)
    paired_ttest.to_csv(outputs["pairedttest"], index=False)



    print("\n✔ Statistical analysis completed")

    return outputs