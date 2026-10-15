"""Unit tests for ransom note and extension change detection (T-P10-04)."""

import pytest

from src.features.ransom_note import (
    extract_ransom_note_features,
    is_ransom_note_name,
)


def test_is_ransom_note_name():
    assert is_ransom_note_name("how_to_decrypt.html")
    assert is_ransom_note_name("README_FOR_DECRYPT.txt")
    assert is_ransom_note_name("C:\\Users\\Victim\\Desktop\\restore_files_instructions.txt")
    assert is_ransom_note_name("!README!.txt")
    assert not is_ransom_note_name("config.ini")
    assert not is_ransom_note_name("setup.exe")


def test_extract_ransom_note_features_detected():
    report = {
        "dropped": [
            {"name": "HOW_TO_DECRYPT_FILES.txt", "size": 1024},
            {"name": "financial_records.xlsx.locked", "size": 2048},
        ],
        "behavior": {
            "summary": {
                "write_files": ["C:\\Users\\User\\Documents\\resume.docx.wncry"],
                "delete_files": [],
            },
            "processes": [],
        },
        "strings": [
            "Your files have been encrypted with military grade RSA-2048.",
            "Download Tor browser and visit http://c2portal.onion to pay bitcoin ransom.",
            "Contact support with your private key.",
        ],
    }

    feat = extract_ransom_note_features(report, sample_id="ransom_sample")
    assert feat.ransom_note_count >= 1
    assert feat.ransom_keyword_hits >= 3
    assert feat.suspicious_extension_count >= 2  # .locked, .wncry
    assert feat.double_extension_count >= 2      # .xlsx.locked, .docx.wncry
    assert feat.ransom_note_detected is True
    assert feat.features_vector["ransom_note_detected"] == 1.0


def test_extract_ransom_note_features_clean():
    clean_report = {
        "dropped": [{"name": "app_update.dll"}],
        "behavior": {
            "summary": {"write_files": ["C:\\Windows\\Temp\\log.txt"]},
            "processes": [],
        },
        "strings": ["Microsoft Windows Operating System", "Copyright 2024"],
    }

    feat = extract_ransom_note_features(clean_report, sample_id="clean_sample")
    assert feat.ransom_note_count == 0
    assert feat.ransom_keyword_hits == 0
    assert feat.suspicious_extension_count == 0
    assert feat.ransom_note_detected is False
    assert feat.features_vector["ransom_note_detected"] == 0.0
