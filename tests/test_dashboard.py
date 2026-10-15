"""Unit tests for Streamlit Dashboard components and data retrieval (T-P8-03, T-P8-04, T-P8-05)."""

from pathlib import Path
import pytest
import pandas as pd

from src.app.alert_db import log_alert, get_alerts_dataframe, update_alert_status
from src.app.api import RansomwareInferenceEngine


def test_alert_database_crud(tmp_path):
    test_db = tmp_path / "test_alerts.db"

    # 1. Log alert
    alert_id = log_alert(
        sample_id="test_sample_123",
        verdict="ransomware",
        confidence=0.985,
        top_reason="Alters memory protection to RWX",
        category="Defense Evasion",
        mitre_technique="T1055.002",
        status="NEW",
        db_path=test_db,
    )
    assert alert_id > 0

    # 2. Retrieve alerts
    df = get_alerts_dataframe(db_path=test_db)
    assert len(df) == 1
    assert df.iloc[0]["sample_id"] == "test_sample_123"
    assert df.iloc[0]["verdict"] == "ransomware"
    assert df.iloc[0]["confidence"] == pytest.approx(0.985)
    assert df.iloc[0]["status"] == "NEW"

    # 3. Update status
    update_alert_status(
        alert_id=alert_id,
        status="QUARANTINED",
        analyst_notes="Verified LockBit dropper.",
        db_path=test_db,
    )

    df_updated = get_alerts_dataframe(db_path=test_db)
    assert df_updated.iloc[0]["status"] == "QUARANTINED"
    assert df_updated.iloc[0]["analyst_notes"] == "Verified LockBit dropper."


def test_dashboard_file_exists():
    dash_app = Path("dashboard/app.py")
    assert dash_app.exists()
    assert dash_app.stat().st_size > 1000
