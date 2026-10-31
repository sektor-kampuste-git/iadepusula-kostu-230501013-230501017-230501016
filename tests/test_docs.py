"""Belge denetimi bozuk bağlantı ve sahte/eksik kanıtı görünür kılmalı."""

import copy
import json
from pathlib import Path

from scripts.check_docs import check, markdown_errors, registry_errors

ROOT = Path(__file__).resolve().parents[1]


def test_repository_documentation_is_consistent():
    assert check(ROOT)["errors"] == []


def test_missing_link_is_reported_but_external_fragment_and_code_are_ignored(tmp_path):
    path = tmp_path / "README.md"
    path.write_text(
        "[dış](https://example.org) [başlık](#başlık)\n"
        "\x60\x60\x60text\n[örnek](eksik-ornek.md)\n\x60\x60\x60\n"
        "[kırık](eksik.md)\n[referans]: olmayan.md\n",
        encoding="utf-8",
    )
    errors = markdown_errors(tmp_path, path)
    assert len(errors) == 2
    assert "eksik.md" in errors[0]
    assert "olmayan.md" in errors[1]


def test_relative_escaping_and_local_file_uri_are_rejected(tmp_path):
    path = tmp_path / "README.md"
    path.write_text("[kaçış](../other.md) [dosya](file:///private.txt)", encoding="utf-8")
    errors = markdown_errors(tmp_path, path)
    assert len(errors) == 2
    assert all("geçersiz" in row for row in errors)


def test_existing_encoded_path_with_spaces_is_allowed(tmp_path):
    (tmp_path / "alt klasör").mkdir()
    (tmp_path / "alt klasör" / "kanıt.md").write_text("kanıt", encoding="utf-8")
    path = tmp_path / "README.md"
    path.write_text("[kanıt](<alt%20klasör/kanıt.md#bölüm>)", encoding="utf-8")
    assert markdown_errors(tmp_path, path) == []


def test_registry_rejects_missing_evidence_unknown_status_and_duplicate_ids():
    original = json.loads((ROOT / "docs/proje_kriterleri.json").read_text(encoding="utf-8"))
    broken = copy.deepcopy(original)
    broken["criteria"][0]["evidence"] = ["olmayan.py"]
    broken["criteria"][0]["status"] = "guaranteed_full_marks"
    broken["criteria"][1]["id"] = "C1"
    errors = registry_errors(ROOT, broken)
    assert any("bulunamayan kanıt" in row for row in errors)
    assert any("bilinmeyen durum" in row for row in errors)
    assert any("birer kez" in row for row in errors)
