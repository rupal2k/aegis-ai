import pandas as pd
import pytest

from ml_engine.training import train


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
