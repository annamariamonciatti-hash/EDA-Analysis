# -*- coding: utf-8 -*-

import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox

SAMPLING_RATE = 4
ALL_PHASES = ["baseline", "control", "cognitive", "stress", "post-stress"]

# Cambia solo questa quando crei una nuova versione
PIPELINE_VERSION = "v_7"


def find_existing_features(database_dir, subject_id):

    processed_dir = os.path.join(
        database_dir, subject_id, "csvs_merged", "processed_eda"
    )

    if not os.path.isdir(processed_dir):
        return None

    pattern = re.compile(
        rf"^eda_features_{re.escape(subject_id)}v(\d+)\.csv$"
    )

    candidates = []

    for filename in os.listdir(processed_dir):
        match = pattern.match(filename)
        if match:
            candidates.append((
                int(match.group(1)),
                os.path.join(processed_dir, filename)
            ))

    if not candidates:
        return None

    return max(candidates, key=lambda x: x[0])


def get_pipeline_config():

    root = tk.Tk()
    root.title(
        f"EDA Pipeline Configuration - {PIPELINE_VERSION}"
    )
    root.geometry("700x330")

    result = {}
    phase_entries = {}
    phase_vars = {}

    # =====================================================
    # DATABASE
    # =====================================================

    tk.Label(
        root,
        text="Database folder"
    ).grid(
        row=0,
        column=0,
        padx=10,
        pady=8
    )

    database_entry = tk.Entry(
        root,
        width=45
    )

    database_entry.grid(
        row=0,
        column=1,
        padx=10,
        pady=8
    )

    def browse():

        folder = filedialog.askdirectory(
            title="Select database folder"
        )

        if folder:
            database_entry.delete(
                0,
                tk.END
            )
            database_entry.insert(
                0,
                folder
            )

    tk.Button(
        root,
        text="Browse",
        command=browse
    ).grid(
        row=0,
        column=2,
        padx=10
    )

    # =====================================================
    # SUBJECT
    # =====================================================

    tk.Label(
        root,
        text="Subject ID"
    ).grid(
        row=1,
        column=0,
        padx=10,
        pady=5
    )

    subject_entry = tk.Entry(
        root,
        width=20
    )

    subject_entry.grid(
        row=1,
        column=1,
        sticky="w",
        padx=10
    )

    # =====================================================
    # HEADER
    # =====================================================

    for col, text in enumerate(
        ["Use", "Phase", "Start", "End"]
    ):

        tk.Label(
            root,
            text=text
        ).grid(
            row=2,
            column=col,
            padx=8,
            pady=3
        )

    # =====================================================
    # PHASES
    # =====================================================

    for row, phase in enumerate(
        ALL_PHASES,
        start=3
    ):

        var = tk.IntVar(
            master=root,
            value=0
        )

        tk.Checkbutton(
            root,
            variable=var,
            onvalue=1,
            offvalue=0
        ).grid(
            row=row,
            column=0
        )

        tk.Label(
            root,
            text=phase
        ).grid(
            row=row,
            column=1,
            padx=8
        )

        start = tk.Entry(
            root,
            width=18
        )

        end = tk.Entry(
            root,
            width=18
        )

        start.grid(
            row=row,
            column=2
        )

        end.grid(
            row=row,
            column=3
        )

        phase_vars[phase] = var
        phase_entries[phase] = (
            start,
            end
        )

    # =====================================================
    # SUBMIT
    # =====================================================

    def submit():

        database_dir = (
            database_entry.get().strip()
        )

        subject_id = (
            subject_entry.get().strip()
        )

        if not os.path.isdir(database_dir):

            messagebox.showerror(
                "Error",
                "Database folder not found"
            )

            return

        subject_dir = os.path.join(
            database_dir,
            subject_id
        )

        if not os.path.isdir(subject_dir):

            messagebox.showerror(
                "Error",
                f"Subject folder not found:\n{subject_dir}"
            )

            return

        # ---------------------------------------------
        # SELECTED PHASES
        # ---------------------------------------------

        selected = [
            phase
            for phase in ALL_PHASES
            if phase_vars[phase].get() == 1
        ]

        if not selected:

            messagebox.showerror(
                "Error",
                "Select at least one phase"
            )

            return

        # ---------------------------------------------
        # TIMESTAMPS
        # ---------------------------------------------

        phases = {}

        for phase in selected:

            start_txt = (
                phase_entries[phase][0]
                .get()
                .strip()
            )

            end_txt = (
                phase_entries[phase][1]
                .get()
                .strip()
            )

            if not start_txt or not end_txt:

                messagebox.showerror(
                    "Error",
                    f"Both timestamps are required for {phase}"
                )

                return

            try:

                start = int(start_txt)
                end = int(end_txt)

            except ValueError:

                messagebox.showerror(
                    "Error",
                    f"Timestamps for {phase} must be integers"
                )

                return

            if end <= start:

                messagebox.showerror(
                    "Error",
                    f"End must be greater than Start for {phase}"
                )

                return

            phases[phase] = {
                "start": start,
                "end": end
            }

        # ---------------------------------------------
        # EXISTING PROCESSING
        # ---------------------------------------------

        existing = find_existing_features(
            database_dir,
            subject_id
        )

        reuse_existing = False
        existing_path = None
        existing_version = None

        if existing is not None:

            existing_version, existing_path = existing

            answer = messagebox.askyesno(
                "Existing processing",
                f"{subject_id} already has processed data "
                f"({existing_version}).\n\n"
                f"Current version: {PIPELINE_VERSION}\n\n"
                "YES = reprocess using the timestamps "
                "entered now\n\n"
                "NO = reuse previous processing"
            )

            reuse_existing = not answer

        # ---------------------------------------------
        # SAVE RESULT
        # ---------------------------------------------

        result.update({

            "database_dir": database_dir,

            "subject_id": subject_id,

            "phases": phases,

            "reuse_existing": reuse_existing,

            "existing_features_path": existing_path,

            "existing_version": existing_version

        })

        root.quit()

    # =====================================================
    # CONFIRM BUTTON
    # =====================================================

    tk.Button(
        root,
        text="CONFIRM",
        command=submit,
        width=20
    ).grid(
        row=len(ALL_PHASES) + 3,
        column=0,
        columnspan=4,
        pady=15
    )

    root.mainloop()
    root.destroy()

    if not result:

        raise RuntimeError(
            "Pipeline configuration cancelled"
        )

    return (
        result["database_dir"],
        result["subject_id"],
        result["phases"],
        result["reuse_existing"],
        result["existing_features_path"],
        result["existing_version"]
    )

 