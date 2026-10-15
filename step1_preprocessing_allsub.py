# -*- coding: utf-8 -*-
"""
Created on Mon Oct  5 12:37:30 2026

@author: Utente
"""

# -*- coding: utf-8 -*-

import os
import matplotlib.pyplot as plt
import neurokit2 as nk
import numpy as np
import pandas as pd

# from scipy.signal import medfilt

from config_eda_allsub import SAMPLING_RATE, PIPELINE_VERSION


def plot_eda(
    signals,
    signal,
    time_seconds,
    markers,
    graphs_dir,
    title,
    filename
):

    plt.figure(figsize=(12, 4))
    plt.plot(time_seconds, signals[signal])

    for marker in markers:
        plt.axvline(marker, color="red")

    plt.title(title)
    plt.xlabel("Time (s)")

    plt.savefig(
        os.path.join(graphs_dir, filename),
        bbox_inches="tight"
    )

    plt.show()


def run_preprocessing(
    database_dir,
    subject_id,
    phases
):

    plt.close("all")

    data_dir = os.path.join(
        database_dir,
        subject_id,
        "csvs_merged"
    )

    file_path = os.path.join(
        data_dir,
        "EDA.csv"
    )

    graphs_dir = os.path.join(
        data_dir,
        f"preliminary_graphs_{PIPELINE_VERSION}"
    )

    processed_dir = os.path.join(
        data_dir,
        "processed_eda"
    )

    os.makedirs(graphs_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)

    print(f"Loading: {file_path}")

    df = pd.read_csv(file_path)

    first_tag = min(
        phase["start"] for phase in phases.values()
    )

    last_tag = max(
        phase["end"] for phase in phases.values()
    )

    df = df[
        (df["ts"] >= first_tag) &
        (df["ts"] <= last_tag)
    ].reset_index(drop=True)

    if df.empty:
        raise ValueError(
            f"No EDA samples found for {subject_id}"
        )

    # eda_raw = medfilt(
    #     df["eda"].values,
    #     kernel_size=3
    # )
    eda_raw = df["eda"].values

    eda_clean = nk.eda_clean(
        eda_raw,
        sampling_rate=SAMPLING_RATE,
        method="neurokit"
    )

    eda_decomp = nk.eda_phasic(
        eda_clean,
        sampling_rate=SAMPLING_RATE,
        method="cvxeda"
    )

    min_len = min(
        len(df),
        len(eda_clean),
        len(eda_decomp)
    )

    df = df.iloc[:min_len].reset_index(drop=True)
    eda_raw = eda_raw[:min_len]
    eda_clean = eda_clean[:min_len]
    eda_decomp = eda_decomp.iloc[:min_len].reset_index(drop=True)

    peaks, info = nk.eda_peaks(
        eda_decomp["EDA_Phasic"],
        sampling_rate=SAMPLING_RATE,
        method="neurokit",
        amplitude_min=0.05
    )

    signals = eda_decomp.copy()

    signals["ts"] = df["ts"].values
    signals["EDA_Raw"] = eda_raw
    signals["EDA_Clean"] = eda_clean

    for column in [
        "SCR_Peaks",
        "SCR_Onsets",
        "SCR_Recovery",
        "SCR_Amplitude"
    ]:
        signals[column] = peaks[column]

    time_seconds = np.arange(len(signals)) / SAMPLING_RATE
    start_timestamp = df["ts"].iloc[0]

    tags = [
        tag
        for phase in phases.values()
        for tag in (phase["start"], phase["end"])
    ]

    phase_markers = [
        (tag - start_timestamp) * 1e-6
        for tag in tags
    ]

    nk.eda_plot(signals, info)

    fig = plt.gcf()
    
    for ax in fig.get_axes():
        for marker in phase_markers:
            ax.axvline(
                x=marker,
                color="red",
                linestyle="-",
                linewidth=1,
                alpha=0.7,
                zorder=5
            )
    
    fig.savefig(
        os.path.join(
            graphs_dir,
            f"eda_{subject_id}_{PIPELINE_VERSION}.svg"
        ),
        bbox_inches="tight"
    )
    
    plt.show()

    output_path = os.path.join(
        processed_dir,
        f"eda_signals_preprocessed_{subject_id}{PIPELINE_VERSION}.csv"
    )

    signals.to_csv(output_path, index=False)

    print(
        f"✔ {subject_id}: signal preprocessed"
    )

    return output_path