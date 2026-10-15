# -*- coding: utf-8 -*-

import os
import shutil

from config_eda_allsub import (
    get_pipeline_config,
    PIPELINE_VERSION
)

from step1_preprocessing_allsub import run_preprocessing
from step2_process_phases_allsub import run_phase_processing
from step3_concatenate_check_allsub import run_concatenate_and_check
from step4_main_stats_allsub import run_stats
from plot_def_allsub import run_plots


def copy_existing_version(
    existing_features_path,
    database_dir,
    subject_id,
    existing_version
):

    processed_dir = os.path.dirname(
        existing_features_path
    )

    new_features = os.path.join(
        processed_dir,
        f"eda_features_{subject_id}{PIPELINE_VERSION}.csv"
    )

    # Current version already exists
    if os.path.abspath(
        existing_features_path
    ) == os.path.abspath(
        new_features
    ):

        print(
            f"✔ {subject_id}: "
            f"{PIPELINE_VERSION} already exists"
        )

        return new_features

    # If current version already exists, use it
    if os.path.exists(new_features):

        print(
            f"✔ {subject_id}: "
            f"{PIPELINE_VERSION} already exists"
        )

        return new_features

    # Copy feature file
    shutil.copy2(
        existing_features_path,
        new_features
    )

    # Copy preprocessed signal if available
    old_signal = os.path.join(
        processed_dir,
        f"eda_signals_preprocessed_"
        f"{subject_id}v{existing_version}.csv"
    )

    new_signal = os.path.join(
        processed_dir,
        f"eda_signals_preprocessed_"
        f"{subject_id}{PIPELINE_VERSION}.csv"
    )

    if (
        not os.path.exists(new_signal)
        and os.path.exists(old_signal)
    ):

        shutil.copy2(
            old_signal,
            new_signal
        )

    print(
        f"✔ {subject_id}: "
        f"copied v{existing_version} "
        f"→ {PIPELINE_VERSION}"
    )

    return new_features


# =========================================================
# PROCESS SUBJECTS
# =========================================================

process_subjects = True
database_dir = None

while process_subjects:

    (
        database_dir,
        subject_id,
        phases,
        reuse_existing,
        existing_features_path,
        existing_version
    ) = get_pipeline_config()

    print("\n" + "=" * 60)
    print(f"SUBJECT: {subject_id}")
    print(f"VERSION: {PIPELINE_VERSION}")
    print(f"PHASES: {list(phases.keys())}")
    print("=" * 60)

    # =====================================================
    # PROCESS / REUSE SUBJECT
    # =====================================================

    if reuse_existing:

        features_path = copy_existing_version(
            existing_features_path,
            database_dir,
            subject_id,
            existing_version
        )

    else:

        # Step 1 - preprocessing
        signals_path = run_preprocessing(
            database_dir,
            subject_id,
            phases
        )

        # Step 2 - phase processing
        features_path = run_phase_processing(
            subject_id,
            phases,
            signals_path
        )

    print(
        f"✔ Features: {features_path}"
    )

    # =====================================================
    # NEXT SUBJECT?
    # =====================================================

    answer = input(
        "\nProcess another subject? [y/n]: "
    ).strip().lower()

    process_subjects = answer == "y"


# =========================================================
# GROUP CONCATENATION
# =========================================================

print("\n" + "=" * 60)
print("GROUP ANALYSIS")
print("=" * 60)

group_path = run_concatenate_and_check(
    database_dir
)


# =========================================================
# STATISTICS
# =========================================================

stats_outputs = run_stats(
    group_path
)


# =========================================================
# PLOTS
# =========================================================

run_plots(
    data_path=group_path,
    sig_path=stats_outputs["wilcoxon"]
)


print("\n✔ PIPELINE COMPLETED")