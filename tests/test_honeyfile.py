"""Unit tests for honeyfile / canary tripwire features (T-P10-03)."""

import pytest

from src.features.honeyfile import (
    extract_honeyfile_features,
    is_canary_path,
)


def test_is_canary_path():
    assert is_canary_path("C:\\Users\\Victim\\Desktop\\canary_doc.docx")
    assert is_canary_path("C:\\Documents\\decoy_passwords.txt")
    assert is_canary_path("C:\\$Recycle.Bin\\S-1-5-21\\trash.bin")
    assert is_canary_path("C:\\Users\\Victim\\Documents\\000_a_test_tripwire.docx")
    assert not is_canary_path("C:\\Windows\\System32\\kernel32.dll")
    assert not is_canary_path("C:\\Program Files\\Mozilla Firefox\\firefox.exe")


def test_extract_honeyfile_features_triggered():
    calls = [
        {"api": "NtOpenFile", "time": 10.0, "arguments": {"filepath": "C:\\Windows\\system.ini"}},
        {"api": "NtCreateFile", "time": 12.5, "arguments": {"filepath": "C:\\Users\\User\\Desktop\\canary_budget.xlsx"}},
        {"api": "NtWriteFile", "time": 13.0, "arguments": {"filepath": "C:\\Users\\User\\Desktop\\canary_budget.xlsx", "entropy": 0.98}},
        {"api": "DeleteFileW", "time": 14.0, "arguments": {"file_name": "C:\\Users\\User\\Desktop\\canary_budget.xlsx"}},
    ]

    feat = extract_honeyfile_features(calls, sample_id="canary_test")
    assert feat.tripwire_triggered is True
    assert feat.time_to_first_trip == 2.5  # 12.5 - 10.0
    assert feat.canary_access_count == 1
    assert feat.canary_write_count == 1
    assert feat.canary_delete_count == 1
    assert feat.max_canary_entropy == 0.98
    assert feat.features_vector["honey_tripwire_triggered"] == 1.0


def test_extract_honeyfile_features_clean_run():
    calls = [
        {"api": "NtOpenFile", "time": 5.0, "arguments": {"filepath": "C:\\Windows\\explorer.exe"}},
        {"api": "NtReadFile", "time": 6.0, "arguments": {"filepath": "C:\\Users\\User\\AppData\\Local\\temp.dat"}},
    ]

    feat = extract_honeyfile_features(calls, sample_id="clean_test")
    assert feat.tripwire_triggered is False
    assert feat.canary_access_count == 0
    assert feat.canary_write_count == 0
    assert feat.features_vector["honey_tripwire_triggered"] == 0.0
    assert feat.features_vector["honey_time_to_trip"] == 999.0
