import pandas as pd
import pytest

from ml_engine.training import train


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
    assert result["hospitalized_count"] >= 2


def test_parse_clinical_note_loss_ratio_increases_with_severity():
    mild_text = (
        "### Instruction: A 30-year-old male with no significant past medical history "
        "was admitted for a routine procedure. ### Response: ..."
    )
    severe_text = (
        "### Instruction: A 75-year-old female with cancer, renal failure, and sepsis "
        "was admitted to the ICU and required mechanical ventilation. ### Response: ..."
    )
    mild = train._parse_clinical_note(mild_text)
    severe = train._parse_clinical_note(severe_text)
    assert severe["loss_ratio"] > mild["loss_ratio"]


def test_parse_clinical_note_defaults_when_age_absent():
    result = train._parse_clinical_note("### Instruction: Patient admitted. ### Response: ...")
    assert 0 < result["age"] < 120


def test_infer_hf_schema_detects_underwriting_tabular():
    df = pd.DataFrame(
        {
            "applicant_age": [38],
            "gender": ["M"],
            "occupation_risk": ["High"],
            "health_score": [43.6],
            "bmi": [22.4],
            "smoker": [False],
            "previous_claims_count": [1],
            "coverage_amount": [250000],
            "premium_calculated": [1948.96],
        }
    )
    assert train.infer_hf_schema(df) == "underwriting_tabular"


def test_infer_hf_schema_detects_insurance_charges():
    df = pd.DataFrame(
        {
            "age": [33],
            "bmi": [33.44],
            "children": [5],
            "sex": ["male"],
            "smoker": ["no"],
            "region": ["southeast"],
            "prediction": [9271.2921],
        }
    )
    assert train.infer_hf_schema(df) == "insurance_charges"


def test_infer_hf_schema_detects_clinical_notes():
    df = pd.DataFrame({"text": ["note"], "summary": ["summary"]})
    assert train.infer_hf_schema(df) == "clinical_notes"


def test_infer_hf_schema_detects_company_profiles():
    df = pd.DataFrame(
        {
            "name": ["Bow Plumbing Group"],
            "industry": ["Plastics"],
            "followers_count": [964],
            "associated_members_count": [66],
            "founded_on": ['{"year": 1939}'],
        }
    )
    assert train.infer_hf_schema(df) == "company_profiles"


def test_map_underwriting_hf_dataframe_returns_aegis_fields():
    df = pd.DataFrame(
        {
            "applicant_age": [38, 53],
            "gender": ["M", "F"],
            "occupation_risk": ["High", "Medium"],
            "health_score": [43.6, 62.3],
            "bmi": [22.4, 31.2],
            "smoker": [False, True],
            "previous_claims_count": [1, 4],
            "coverage_amount": [250000, 100000],
            "premium_calculated": [1948.96, 6116.35],
        }
    )

    mapped = train.map_underwriting_hf_dataframe(df)

    assert len(mapped) == 2
    assert {"age", "avg_daily_steps", "visit_count", "lab_heart_flag", "loss_ratio"} <= set(mapped.columns)
    assert mapped["smoker"].tolist() == [0, 1]
    assert mapped["visit_count"].tolist() == [1.0, 4.0]
    assert mapped["loss_ratio"].gt(0).all()


def test_map_insurance_charge_hf_dataframe_returns_aegis_fields():
    df = pd.DataFrame(
        {
            "age": [33, 58],
            "bmi": [33.44, 25.177],
            "children": [5, 0],
            "sex": ["male", "male"],
            "smoker": ["no", "no"],
            "region": ["southeast", "northeast"],
            "prediction": [9271.29, 11441.76],
        }
    )

    mapped = train.map_insurance_charge_hf_dataframe(df)

    assert len(mapped) == 2
    assert {"age", "avg_daily_steps", "visit_count", "lab_heart_flag", "loss_ratio"} <= set(mapped.columns)
    assert mapped["gender"].tolist() == ["M", "M"]
    assert mapped["smoker"].tolist() == [0, 0]
    assert mapped["loss_ratio"].gt(0).all()
    assert mapped["visit_count"].between(0, 10).all()


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
