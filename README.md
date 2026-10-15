# EDA Multi-Subject Processing and Statistical Analysis Pipeline

## Overview

This repository contains a modular Python pipeline for preprocessing electrodermal activity (EDA) signals, extracting phase-specific physiological features, combining data across participants, performing statistical analyses, and generating visualizations.

The pipeline is designed for experimental studies involving multiple physiological recording phases, including baseline, control, cognitive task, stress, and post-stress conditions.

The workflow supports participant-by-participant processing, reuse of previously processed data, group-level data aggregation, statistical testing, multiple-comparison correction, and automated plotting.

## Repository structure

| File | Description |
|---|---|
| `main_eda_allsub.py` | Main entry point. Coordinates participant processing, group aggregation, statistical analysis, and plotting. |
| `config_eda_allsub.py` | Provides the graphical configuration interface, sampling rate, phase definitions, and pipeline version. |
| `step1_preprocessing_allsub.py` | Loads raw EDA recordings, extracts the selected time interval, cleans the signal, decomposes tonic and phasic components, detects skin conductance responses, and saves diagnostic plots. |
| `step2_process_phases_allsub.py` | Segments preprocessed signals into experimental phases and extracts phase-specific features. |
| `step3_concatenate_check_allsubjects.py` | Combines participant-level feature files into a group dataset and evaluates the association between phase duration and extracted features. |
| `step4_main_stats_allsub.py` | Coordinates group-level statistical analyses and exports their results. |
| `stat_analysis_allsub.py` | Implements repeated-measures statistical tests, post-hoc comparisons, effect-size calculations, and FDR correction. |
| `plot_def_allsub.py` | Generates line plots, boxplots, and violin plots for selected EDA features. |

## Requirements

The pipeline requires Python 3 and the following packages:

- NumPy
- pandas
- Matplotlib
- NeuroKit2
- SciPy
- statsmodels

Tkinter is also required for the graphical configuration interface and is included with many standard Python installations.

Install the dependencies using:

```bash
pip install numpy pandas matplotlib neurokit2 scipy statsmodels
```

If Tkinter is unavailable, install the appropriate package for your operating system or Python distribution.

## Input data and directory structure

The pipeline expects a database directory containing one folder per participant.

Each participant folder must contain a `csvs_merged/` directory with an `EDA.csv` file.

Expected structure:

```text
database/
├── S1/
│   └── csvs_merged/
│       └── EDA.csv
├── S2/
│   └── csvs_merged/
│       └── EDA.csv
└── S3/
    └── csvs_merged/
        └── EDA.csv
```

The raw EDA files must contain at least the following columns:

- `ts`: signal timestamps expressed in microseconds.
- `eda`: raw electrodermal activity measurements.

The timestamps used to define experimental phases must use the same time base and units as the `ts` column.

## Experimental phases

The configuration interface allows the experimenter to select one or more phases and specify their start and end timestamps.

The default phase labels in `config_eda_allsub.py` are:

- `baseline`
- `control`
- `cognitive`
- `stress`
- `post-stress`

The group-level aggregation and statistical modules use the following labels:

- `baseline`
- `control`
- `cognitive`
- `stress`
- `post-stress`

These labels must be consistent across the feature files and the downstream analysis. If different labels are used in the raw experimental workflow, they should be harmonized before group-level analysis.

## Pipeline workflow

### Step 1 — Signal preprocessing

Implemented in `step1_preprocessing_allsub.py`.

For each participant, the script:

1. Loads the raw EDA recording.
2. Selects the time interval spanning the earliest selected phase start and the latest selected phase end.
3. Cleans the signal using `nk.eda_clean()` with the NeuroKit method.
4. Decomposes the signal into tonic and phasic components using `nk.eda_phasic()` with the CVXEDA method.
5. Detects skin conductance response (SCR) peaks using `nk.eda_peaks()`.
6. Adds raw, cleaned, decomposed, and event-related signals to the processed dataset.
7. Generates and saves a diagnostic EDA plot with phase-boundary markers.

The sampling rate is configured in `config_eda_allsub.py` and defaults to 4 Hz.

### Step 2 — Phase-specific feature extraction

Implemented in `step2_process_phases_allsub.py`.

The preprocessed signal is segmented using the start and end timestamps specified for each selected phase.

The extracted features include:

| Feature | Description |
|---|---|
| `EDA_Tonic_Median` | Median tonic EDA level during the phase. |
| `EDA_Tonic_Mean` | Mean tonic EDA level during the phase. |
| `EDA_Phasic_Max` | Maximum phasic EDA value during the phase. |
| `EDA_Phasic_STD` | Standard deviation of the phasic EDA signal during the phase. |
| `SCR_Rate` | Number of detected SCR peaks per estimated phase duration in seconds. |
| `EDA_SympatheticN` | Normalized sympathetic activity index estimated using NeuroKit2. |

Additional interval-related features are obtained through NeuroKit2's `eda_intervalrelated()` function, subject to the columns retained by the processing script.

The resulting participant-level feature table contains the experimental condition, phase duration, and participant identifier.

### Step 3 — Group aggregation and duration sensitivity analysis

Implemented in `step3_concatenate_check_allsubjects.py`.

The pipeline collects participant-level feature files corresponding to the configured pipeline version and combines them into a single group-level CSV.

It also evaluates the association between phase duration and selected EDA features using Spearman's rank correlation.

For each condition-feature combination, the analysis records:

- Spearman's correlation coefficient (\(\rho\)).
- The corresponding p-value.
- The number of valid observations.

Combinations with fewer than five valid observations are excluded from this sensitivity analysis.

This analysis helps assess whether differences in recording duration may be associated with the extracted physiological features. It does not, by itself, establish that duration has no influence when the correlation is nonsignificant.

### Step 4 — Statistical analysis

Implemented in `step4_main_stats_allsub.py` and `stat_analysis_allsub.py`.

The pipeline performs complementary repeated-measures analyses.

**Friedman test**

A non-parametric test used to evaluate differences across repeated experimental conditions.

**Repeated-measures ANOVA**

A parametric analysis used to evaluate within-subject differences across conditions.

**Wilcoxon signed-rank post-hoc tests**

Pairwise comparisons for features showing a significant omnibus Friedman test.

**Paired-samples t-test post-hoc comparisons**

Pairwise comparisons for features showing a significant repeated-measures ANOVA.

**Multiple-comparison correction**

The Benjamini–Krieger–Yekutieli procedure is applied using the `fdr_tsbky` method, with an alpha level of 0.05.

The statistical functions use complete participant-level observations across the conditions included in each test. Consequently, the number of participants may differ between features depending on missing data.

Effect-size estimates are also calculated for the pairwise comparisons.

### Step 5 — Visualization

Implemented in `plot_def_allsub.py`.

The plotting module generates three types of figures for the selected features:

- **Line plots:** display individual participant trajectories across conditions.
- **Boxplots:** summarize the distribution of feature values in each condition and display significance annotations from the Wilcoxon post-hoc results.
- **Violin plots:** visualize the distribution of feature values in each condition.

The output figures are saved as high-resolution PNG files.

## Running the pipeline

Run the main script:

```bash
python main_eda_allsub.py
```

For each participant, the graphical interface prompts the experimenter to:

1. Select the database directory.
2. Enter the participant identifier.
3. Select the experimental phases to process.
4. Enter the start and end timestamps for each selected phase.
5. Decide whether to reprocess the participant or reuse existing feature data when available.

After processing each participant, the script asks whether another participant should be processed.

When participant processing is complete, the pipeline automatically runs group aggregation, duration sensitivity analysis, statistical testing, and plotting.

## Reusing previously processed data

When existing participant-level feature files are detected, the configuration interface allows the experimenter to reuse previous processing rather than recomputing features.

The main script copies the existing feature file to the current version's filename and, if available, also copies the corresponding preprocessed signal file.

**Important:** reusing existing data changes their filename and version label; it does not recompute features using the newly entered phase timestamps. The reused features therefore retain the assumptions and phase boundaries of the original processing.

Verify that the existing feature file is compatible with the current pipeline version before reusing it.

## Output files

The pipeline creates the following outputs.

### Participant-level outputs

Within each participant's `csvs_merged/` directory:

```text
csvs_merged/
├── preliminary_graphs_v_7/
│   └── eda_S1_v_7.svg
└── processed_eda/
    ├── eda_signals_preprocessed_S1v_7.csv
    └── eda_features_S1v_7.csv
```

The example filenames use participant `S1` and the default version identifier `v_7`.

### Group-level outputs

Within `Subjects_EDA/`:

```text
Subjects_EDA/
├── all_subjects_eda_v_7.csv
├── duration_sensitivityv_7.csv
├── stats_results_eda_friedmanv_7.csv
├── posthoc_results_eda_wilkoxonv_7.csv
├── stats_results_eda_anovav_7.csv
├── posthoc_results_eda_pairedttestv_7.csv
└── plots/
    └── v_7/
        ├── EDA_Tonic_Mean_line_v_7.png
        ├── EDA_Tonic_Mean_box_v_7.png
        └── EDA_Tonic_Mean_violin_v_7.png
```

The output directory is created automatically when needed. The names shown above are illustrative; actual output depends on the selected features and available data.

## Version management

The pipeline version is configured in `config_eda_allsub.py`:

```python
PIPELINE_VERSION = "v_7"
```

Update this value when creating a new processing version.

The version identifier is used in output filenames to distinguish processing runs and reduce the risk of unintentionally overwriting earlier outputs.

Version labels do not replace proper documentation of changes to preprocessing, feature extraction, or statistical methods.

## Data protection and reproducibility

This pipeline is intended for research use.

Before running the analysis, verify timestamp units, phase definitions, sampling rate, participant identifiers, and data completeness.

Keep raw recordings unchanged and maintain backups of previously processed data. Check the output files and statistical assumptions before interpreting the results.

If the repository is shared publicly, do not include identifiable participant data, raw recordings, credentials, or other confidential information.

## Acknowledgements

This project uses the following open-source scientific Python libraries:

- [NeuroKit2](https://github.com/neuropsychology/NeuroKit)
- [NumPy](https://numpy.org/)
- [pandas](https://pandas.pydata.org/)
- [Matplotlib](https://matplotlib.org/)
- [SciPy](https://scipy.org/)
- [statsmodels](https://www.statsmodels.org/)
