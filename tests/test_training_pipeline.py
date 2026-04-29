import pandas as pd
import pytest

from ml_engine.training import train


# ── Clinical notes parser ────────────────────────────────────────────────────

def test_parse_clinical_note_extracts_age_and_gender():
    text = (
        "### Instruction: Hospital Course: A 67-year-old male presented with chest pain. "
        "He was diagnosed with hypertension. ### Response: ..."
    )
    result = train._parse_clinical_note(text)
    assert result["age"] == 67.0
    assert result["gender"] == "M"


def test_parse_clinical_note_detects_conditions():
    text = (
        "### Instruction: A 55-year-old female with diabetes mellitus and hypertension "
        "was admitted to the ICU with pneumonia. She was a current smoker. ### Response: ..."
    )
    result = train._parse_clinical_note(text)
    assert result["diabetic"] == 1
    assert result["hypertension"] == 1
    assert result["smoker"] == 1
    assert result["hospitalized_count"] >= 2   # regular + ICU


def test_parse_clinical_note_loss_ratio_increases_with_severity():
    mild_text = (
        "### Instruction: A 30-year-old male with no significant past medical history "
        "was admitted for a routine procedure. ### Response: ..."
    )
    severe_text = (
        "### Instruction: A 75-year-old female with cancer, renal failure, and sepsis "
        "was admitted to the ICU and required mechanical ventilation. ### Response: ..."
    )
    mild   = train._parse_clinical_note(mild_text)
    severe = train._parse_clinical_note(severe_text)
    assert severe["loss_ratio"] > mild["loss_ratio"]


def test_parse_clinical_note_defaults_when_age_absent():
    text = "### Instruction: Patient admitted. ### Response: ..."
    result = train._parse_clinical_note(text)
    assert 0 < result["age"] < 120


# ── Dataset loading / combining ──────────────────────────────────────────────

def test_resolve_dataset_mode_defaults_to_both():
    args = train.build_arg_parser().parse_args([])
    assert train.resolve_dataset_mode(args) == "both"


def test_resolve_dataset_mode_supports_legacy_hf_flag():
    args = train.build_arg_parser().parse_args(["--use-hf-dataset"])
    assert train.resolve_dataset_mode(args) == "hf"


def test_hf_dataset_argument_defaults_to_configured_dataset():
    args = train.build_arg_parser().parse_args([])
    assert args.hf_dataset == train.HF_DATASET_NAME


def test_hf_dataset_argument_can_be_overridden():
    args = train.build_arg_parser().parse_args(["--hf-dataset", "owner/custom-dataset"])
    assert args.hf_dataset == "owner/custom-dataset"


def test_load_training_dataframe_combines_local_and_hf(monkeypatch):
    local_df = pd.DataFrame({"loss_ratio": [0.4], "age": [30]})
    hf_df = pd.DataFrame({"loss_ratio": [0.8, 1.1], "age": [40, 50]})

    monkeypatch.setattr(train, "load_local_dataset", lambda: local_df)
    monkeypatch.setattr(train, "load_from_huggingface", lambda dataset_name=train.HF_DATASET_NAME: hf_df)

    combined, source_counts = train.load_training_dataframe("both")

    assert len(combined) == 3
    assert source_counts == {"local": 1, "huggingface": 2}
    assert combined["dataset_source"].tolist() == ["local", "huggingface", "huggingface"]


def test_load_training_dataframe_falls_back_to_remaining_source(monkeypatch, capsys):
    local_df = pd.DataFrame({"loss_ratio": [0.4], "age": [30]})

    monkeypatch.setattr(train, "load_local_dataset", lambda: local_df)

    def raise_hf_error(dataset_name=train.HF_DATASET_NAME):
        raise RuntimeError("HF unavailable")

    monkeypatch.setattr(train, "load_from_huggingface", raise_hf_error)

    combined, source_counts = train.load_training_dataframe("both")
    captured = capsys.readouterr()

    assert len(combined) == 1
    assert source_counts == {"local": 1}
    assert "WARNING: Failed to load huggingface dataset: HF unavailable" in captured.out


def test_load_training_dataframe_raises_for_single_source_failure(monkeypatch):
    def raise_hf_error(dataset_name=train.HF_DATASET_NAME):
        raise RuntimeError("HF unavailable")

    monkeypatch.setattr(train, "load_from_huggingface", raise_hf_error)

    with pytest.raises(RuntimeError, match="HF unavailable"):
        train.load_training_dataframe("hf")
