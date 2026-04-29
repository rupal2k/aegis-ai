# Aegis AI — Hugging Face Dataset Integration Guide

## Overview

The Aegis AI model training pipeline now supports loading training data directly from the Hugging Face Hub. This enables access to the comprehensive insurance underwriting risk dataset hosted at:

**Dataset:** `OMG091213/gcc-insurance-underwriting-risk`

---

## Quick Start

### 1. Install Dependencies

The `datasets` package has been added to `requirements.txt` and `requirements.docker.txt`. Install it:

```bash
pip install datasets>=2.15.0
```

### 2. Train with Hugging Face Data

Run the training script with the `--use-hf-dataset` flag:

```bash
python -m ml_engine.training.train --use-hf-dataset
```

### 3. Train with Local Data (Default)

To use the existing local CSV training data, run without the flag:

```bash
python -m ml_engine.training.train
```

---

## Dataset Details

### Source
- **Provider:** Hugging Face Hub
- **Dataset ID:** `OMG091213/gcc-insurance-underwriting-risk`
- **Documentation:** https://huggingface.co/datasets/OMG091213/gcc-insurance-underwriting-risk

### Expected Features

The dataset should contain the following columns (or a compatible subset):

**Demographics:**
- `age` — Employee age (years)
- `gender` — Gender (M/F)
- `bmi` — Body Mass Index
- `smoker` — Smoking status (0/1)
- `diabetic` — Diabetes diagnosis (0/1)
- `hypertension` — Hypertension diagnosis (0/1)

**Telemetry & Activity:**
- `avg_daily_steps` — Average daily steps
- `step_volatility` — Step count variability
- `avg_resting_hr` — Average resting heart rate
- `hr_trend` — Heart rate trend
- `avg_active_mins` — Average active minutes
- `avg_sleep_hours` — Average sleep duration
- `avg_spo2` — Average blood oxygen saturation

**Clinical:**
- `visit_count` — Number of medical visits
- `hospitalized_count` — Number of hospitalizations

**Lab Results:**
- `lab_heart_flag` — Cardiac abnormality indicator
- `lab_inflammation_flag` — Inflammation indicator
- `lab_diabetes_flag` — Diabetes marker indicator
- `lab_kidney_flag` — Kidney function indicator
- `lab_liver_flag` — Liver function indicator
- `lab_iron_flag` — Iron level indicator
- `lab_thyroid_flag` — Thyroid function indicator
- `lab_bone_flag` — Bone health indicator
- `lab_vitamin_flag` — Vitamin deficiency indicator

**Target:**
- `loss_ratio` — Loss ratio (claims / premiums) — used to derive the training target

### Data Preprocessing

The training pipeline automatically:
1. Engineers derived features (activity_score, health_composite, interactions)
2. Fills missing values with sensible defaults
3. Aggregates lab features into domain-level risk scores
4. Log-transforms the target variable for better model fit

---

## Using the Dataset in Python

### Direct Dataset Access

You can also load and work with the dataset directly in your own scripts:

```python
from datasets import load_dataset

# Load the dataset
ds = load_dataset("OMG091213/gcc-insurance-underwriting-risk")

# Convert to pandas
df = ds['train'].to_pandas()

# View shape and columns
print(f"Shape: {df.shape}")
print(f"Columns: {list(df.columns)}")

# Use with Aegis feature engineering
from ml_engine.features import engineer_features, get_feature_matrix

df_engineered = engineer_features(df)
X, y, feature_names = get_feature_matrix(df_engineered)
```

### Data Splits

The HF dataset loads into a single train split. The training pipeline then applies:
- 80% training (further split into 90% train / 10% validation for early stopping)
- 20% test set
- Stratified split based on loss_ratio quartiles

---

## Comparing Local vs. Hugging Face Training

Both data sources go through the same feature engineering and training pipeline:

| Step | Local CSV | Hugging Face |
|------|-----------|--------------|
| Load data | `data/output/training_dataset.csv` | HF Hub API |
| Feature engineering | ✓ | ✓ |
| Train/test split | 80/20 stratified | 80/20 stratified |
| Hyperparameter tuning | Optuna (30 trials) | Optuna (30 trials) |
| Model training | XGBoost + early stopping | XGBoost + early stopping |
| Metrics logging | MLflow | MLflow |

---

## Troubleshooting

### Dataset Not Found

```
HTTPError: 401 Unauthorized
```

**Solution:** The dataset may require authentication. Try:
```bash
pip install datasets --upgrade
python -c "from datasets import load_dataset; load_dataset('OMG091213/gcc-insurance-underwriting-risk')"
```

### Out of Memory

If the dataset is very large, consider:
1. Using `streaming=True` in load_dataset (requires code modification)
2. Sampling a subset of rows
3. Using a machine with more RAM
4. Using cloud compute (Google Colab, AWS, etc.)

### Missing Columns

If the HF dataset has different columns, you may need to adapt `ml_engine/features.py` to map the HF columns to the expected format. The feature engineering is designed to be flexible with missing columns (it fills them with sensible defaults).

---

## Integration with MLflow

All training runs (local or HF data) are logged to MLflow:

1. **Start MLflow UI:**
   ```bash
   mlflow ui --backend-store-uri http://localhost:5000
   ```

2. **View runs:**
   - Open http://localhost:5000
   - Compare metrics, params, and artifacts across runs
   - Data source is logged in the `data_source` tag

---

## Adding More Datasets

To add another Hugging Face dataset, modify `load_from_huggingface()` in `ml_engine/training/train.py`:

```python
def load_from_huggingface():
    """Load dataset from Hugging Face"""
    from datasets import load_dataset
    
    # Replace with your dataset
    ds = load_dataset("YOUR_DATASET_ID")
    df = ds['train'].to_pandas()
    return df
```

---

## Performance Expectations

Training with the HF dataset should produce similar or better model performance compared to the local synthetic data:

- **Expected Test MAE:** < 0.45 (on log-scaled loss ratio)
- **Expected Test R²:** > 0.75
- **Training time:** ~3-5 minutes (30 Optuna trials)
- **Model artifacts:** Saved to `ml_engine/artifacts/`

---

## Next Steps

1. Install `datasets`: `pip install datasets>=2.15.0`
2. Run training: `python -m ml_engine.training.train --use-hf-dataset`
3. View results in MLflow: `mlflow ui`
4. Use the trained model in inference: `python ingestion/main.py`

For questions or issues, refer to the dataset README or open an issue on the Hugging Face Hub.
