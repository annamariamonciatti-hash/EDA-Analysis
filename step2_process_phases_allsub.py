# -*- coding: utf-8 -*-

import os
import neurokit2 as nk
import pandas as pd

from config_eda_allsub import (
    SAMPLING_RATE,
    PIPELINE_VERSION
)


def run_phase_processing(
    subject_id,
    phases,
    signals_path
):

    signals = pd.read_csv(signals_path)
    base_dir = os.path.dirname(signals_path)
    results = []

    for label, tags in phases.items():

        print(f"Processing: {label}")

        seg = signals[
            (signals["ts"] >= tags["start"]) &
            (signals["ts"] <= tags["end"])
        ]

        if seg.empty:
            print(f"⚠️ Empty segment: {label}")
            continue

        duration_sec = len(seg) / SAMPLING_RATE
        feat = pd.DataFrame()

        feat["EDA_Tonic_Median"] = [seg["EDA_Tonic"].median()]
        feat["EDA_Tonic_Mean"] = [seg["EDA_Tonic"].mean()]
        feat["EDA_Phasic_Max"] = [seg["EDA_Phasic"].max()]
        feat["EDA_Phasic_STD"] = [seg["EDA_Phasic"].std()]

        scr_count = seg["SCR_Peaks"].sum()
        feat["SCR_Rate"] = [scr_count / duration_sec]

        feat_interval = nk.eda_intervalrelated(
            seg,
            sampling_rate=SAMPLING_RATE
        )

        feat_interval = feat_interval.drop(
            columns=[
                "SCR_Peaks_N",
                "SCR_Peaks_Amplitude_Mean"
            ],
            errors="ignore"
        )

        feat_symp = pd.DataFrame([
            nk.eda_sympathetic(
                seg["EDA_Phasic"],
                sampling_rate=SAMPLING_RATE,
                frequency_band=[0.045, 0.25],
                method="posada",
                show=False
            )
        ])

        feat_interval = feat_interval.drop(
            columns=[
                "EDA_Sympathetic",
                "EDA_SympatheticN"
            ],
            errors="ignore"
        )

        feat_symp = feat_symp[
            ["EDA_SympatheticN"]
        ]

        feat = pd.concat(
            [feat, feat_interval, feat_symp],
            axis=1
        )

        feat = feat.loc[
            :, ~feat.columns.duplicated()
        ]

        feat["condition"] = label
        feat["duration_sec"] = duration_sec
        feat["subject"] = subject_id

        results.append(feat)

    if not results:
        raise ValueError(
            f"No valid phase found for {subject_id}"
        )

    results_df = pd.concat(
        results,
        ignore_index=True
    )

    output_path = os.path.join(
        base_dir,
        f"eda_features_{subject_id}{PIPELINE_VERSION}.csv"
    )

    results_df.to_csv(
        output_path,
        index=False
    )

    print(
        f"✔ Features saved: {output_path}"
    )

    return output_path