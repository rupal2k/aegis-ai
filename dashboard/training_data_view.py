"""Training Data tab — append flexible CSVs to the training dataset and optionally retrain."""
import subprocess
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from data.upload_training_data import (
    DATASET_PATH, BACKUP_DIR, CANONICAL_COLS, ALIASES, process, append_to_dataset,
)
from dashboard.design_helpers import (
    section_header, empty_state, inline_note, ICON_UPLOAD, ICON_DATA,
)


def _alias_table() -> str:
    rows = []
    for canonical in CANONICAL_COLS:
        accepted = [canonical] + ALIASES.get(canonical, [])
        rows.append(f"| `{canonical}` | {', '.join(f'`{a}`' for a in accepted)} |")
    return "| Canonical | Accepted variants |\n|---|---|\n" + "\n".join(rows)


def render_tab() -> None:
    section_header(
        "Model Operations",
        "Training data uploader",
        "Upload any CSV with employee health, claims, or wearable context. Columns are auto-mapped "
        "via aliases; missing fields are filled from existing-dataset medians. New rows are appended "
        f"to <code>{DATASET_PATH}</code> for the next training run.",
    )

    if not DATASET_PATH.exists():
        inline_note(
            f"<b>{DATASET_PATH}</b> not found — run the data pipeline first before uploading training data.",
            level="error",
        )
        return

    with st.expander("Accepted column names (aliases)", expanded=False):
        st.markdown(
            "**Required:** something matching `loss_ratio` (the target) — or both `total_claims` "
            "and `premium_share` so it can be derived. Everything else is optional."
        )
        st.markdown(_alias_table())

    uploaded = st.file_uploader(
        "Upload training CSV",
        type=["csv"],
        help="Any column ordering or naming — the system auto-maps and fills missing fields.",
    )

    if not uploaded:
        empty_state(
            title="Drop a training CSV to begin",
            hint="Any column ordering or naming is fine — the system fuzzy-matches against canonical "
                 "fields and fills the rest from the existing dataset. Only loss_ratio (or claims+premium "
                 "to derive it) is mandatory.",
            icon_svg=ICON_UPLOAD,
            cta="Expand the alias table above to see accepted column names",
        )
        return

    try:
        df_raw = pd.read_csv(uploaded)
    except Exception as exc:
        inline_note(f"Could not parse CSV — {exc}", level="error")
        return

    st.caption(f"Read **{len(df_raw):,}** rows / **{len(df_raw.columns)}** columns from upload.")

    reference = pd.read_csv(DATASET_PATH)
    canonical, report = process(df_raw, reference)

    if report["errors"]:
        inline_note("Validation failed — fix the issues below and re-upload:", level="error")
        for err in report["errors"]:
            st.markdown(f"- {err}")
        return

    c1, c2, c3 = st.columns(3)
    c1.metric("Mapped columns", len(report["mapping"]))
    c2.metric("Defaulted columns", len(report["filled_with_defaults"]))
    c3.metric("Ignored columns", len(report["unmapped"]))

    with st.expander("Mapping detail", expanded=False):
        if report["mapping"]:
            st.markdown("**Recognized columns:**")
            for src, dst in report["mapping"].items():
                st.caption(f"`{src}` → `{dst}`")
        if report["filled_with_defaults"]:
            st.markdown("**Filled with dataset defaults:**")
            st.caption(", ".join(f"`{c}`" for c in report["filled_with_defaults"]))
        if report["unmapped"]:
            st.markdown("**Ignored (no canonical match):**")
            st.caption(", ".join(f"`{c}`" for c in report["unmapped"]))

    st.markdown("**Preview (first 5 rows after canonicalisation):**")
    st.dataframe(canonical.head(5), use_container_width=True, hide_index=True)

    col_a, col_b = st.columns(2)
    backup     = col_a.checkbox("Back up existing dataset before append", value=True)
    do_retrain = col_b.checkbox("Retrain model after append (slow — runs Optuna)", value=False)

    if st.button(
        f"Append {len(canonical):,} rows to training dataset",
        type="primary",
        use_container_width=True,
    ):
        try:
            new_total = append_to_dataset(canonical, backup=backup, dry_run=False)
            inline_note(
                f"Appended <b>{len(canonical):,}</b> rows. Dataset now has <b>{new_total:,}</b> total rows.",
                level="ok",
            )
        except Exception as exc:
            inline_note(f"Append failed: {exc}", level="error")
            return

        if do_retrain:
            with st.status("Retraining model — this can take several minutes...", expanded=True) as status:
                proc = subprocess.run(
                    [sys.executable, "-m", "ml_engine.training.train"],
                    cwd=Path.cwd(),
                    capture_output=True,
                    text=True,
                )
                if proc.stdout:
                    st.code(proc.stdout[-4000:], language="text")
                if proc.returncode == 0:
                    status.update(label="Training complete.", state="complete")
                    st.success("Model retrained. Restart the API to pick up the new artifact.")
                else:
                    status.update(label=f"Training failed (exit {proc.returncode}).", state="error")
                    if proc.stderr:
                        st.code(proc.stderr[-2000:], language="text")
