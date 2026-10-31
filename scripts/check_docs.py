"""Ağsız belge bağlantısı ve gereksinim kanıt kontrolü; uyum/not ölçümü değildir."""

import argparse
import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

EXCLUDED = {".git", ".venv", ".local", "artifacts", "build", "dist", "__pycache__"}
REQUIRED = (
    "README.md",
    "SPEC.md",
    "TESLIM.md",
    "docs/README.md",
    "docs/mimari.md",
    "docs/ekip_calisma_rehberi.md",
    "docs/kodu_anlama_rehberi.md",
    "docs/kullanim_senaryosu.md",
    "docs/model_karti.md",
    "src/README.md",
    "data/README.md",
    "eval/README.md",
    "tests/README.md",
    "scripts/README.md",
    ".github/OTOMASYON.md",
    ".streamlit/README.md",
)
STATUSES = {"implemented", "partial", "pending"}


def local_target(root: Path, parent: Path, target: str) -> Path:
    """Mutlak veya depo dışına taşan yerel kanıt/bağlantı yolunu reddet."""
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or "\\" in target:
        raise ValueError("Yerel yol göreli olmalı")
    path = unquote(parsed.path)
    if not path or Path(path).is_absolute():
        raise ValueError("Yerel yol boş veya mutlak")
    resolved = (parent / path).resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError("Yerel yol depo dışına çıkıyor")
    return resolved


def markdown_errors(root: Path, path: Path) -> list[str]:
    """Kod blokları dışındaki satır içi ve referans yerel bağlantıları doğrula."""
    errors = []
    active = []
    fence = None
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        marker = re.match(r"^\s*(\`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)[0]
            if fence is None:
                fence = token
            elif fence == token:
                fence = None
            continue
        if fence is None:
            active.append(line)
    text = "\n".join(active)
    targets = re.findall(r"!?\[[^\]\n]*\]\(\s*(<[^>]+>|[^\s)]+)", text)
    targets += re.findall(r"^\s*\[[^\]]+\]:\s*(<[^>]+>|\S+)", text, flags=re.M)
    for target in targets:
        target = target.strip("<>")
        if target.startswith("#"):
            continue
        parsed = urlsplit(target)
        if parsed.scheme in {"https", "http", "mailto"}:
            continue  # Ağ erişimi veya dış bağlantı doğruluğu bu kontrolün kapsamı değil.
        try:
            resolved = local_target(root, path.parent, target)
            if not resolved.exists():
                errors.append(f"{path.relative_to(root)}: bulunamayan bağlantı: {target}")
        except ValueError:
            errors.append(f"{path.relative_to(root)}: geçersiz yerel bağlantı: {target}")
    return errors


def registry_errors(root: Path, data: dict) -> list[str]:
    """Sekiz bileşenin durum/sahip/sonraki iş ve mevcut kanıt yollarını kontrol et."""
    errors = []
    if data.get("schema_version") != 1 or not str(data.get("scope", "")).strip():
        errors.append("Kriter listesinde sürüm veya kapsam eksik")
    try:
        date.fromisoformat(data["updated_on"])
    except (KeyError, TypeError, ValueError):
        errors.append("Kriter tarihi ISO takvim tarihi olmalı")
    rows = data.get("criteria")
    if not isinstance(rows, list):
        return [*errors, "Kriter listesi dizi olmalı"]
    ids = [row.get("id") for row in rows if isinstance(row, dict)]
    if len(ids) != 8 or set(ids) != {f"C{i}" for i in range(1, 9)}:
        errors.append("C1-C8 kriterleri birer kez bulunmalı")
    for row in rows:
        if not isinstance(row, dict):
            errors.append("Her kriter nesne olmalı")
            continue
        label = str(row.get("id", "?"))
        if row.get("status") not in STATUSES:
            errors.append(f"{label}: bilinmeyen durum")
        if any(
            not isinstance(row.get(key), str) or not row[key].strip()
            for key in ("title", "owner", "next_action")
        ):
            errors.append(f"{label}: başlık, sahip veya sonraki iş eksik")
        evidence = row.get("evidence")
        if not isinstance(evidence, list) or not evidence:
            errors.append(f"{label}: kanıt yolları eksik")
            continue
        for target in evidence:
            try:
                if not isinstance(target, str) or not local_target(root, root, target).is_file():
                    errors.append(f"{label}: bulunamayan kanıt: {target}")
            except ValueError:
                errors.append(f"{label}: geçersiz kanıt yolu: {target}")
    return errors


def showcase_errors(root: Path) -> list[str]:
    """GitHub'ın ürün README'si yerine otomasyon belgesini seçmesini engelle."""
    github = root / ".github"
    if not github.is_dir():
        return []
    return [
        f"Ana vitrin gölgeleniyor: {p.relative_to(root)}; otomasyon belgesini yeniden adlandırın"
        for p in github.iterdir()
        if p.is_file() and (p.name.casefold() == "readme" or p.stem.casefold() == "readme")
    ]


def check(root: Path) -> dict:
    """Mevcut depoyu tara; harici ağa veya gizli dosyalara erişme."""
    root = root.resolve()
    errors = [f"Zorunlu belge eksik: {p}" for p in REQUIRED if not (root / p).is_file()]
    errors.extend(showcase_errors(root))
    docs = sorted(p for p in root.rglob("*.md") if not set(p.relative_to(root).parts) & EXCLUDED)
    for path in docs:
        errors.extend(markdown_errors(root, path))
    try:
        data = json.loads((root / "docs/proje_kriterleri.json").read_text(encoding="utf-8-sig"))
        if not isinstance(data, dict):
            raise ValueError
        errors.extend(registry_errors(root, data))
    except (OSError, ValueError):
        errors.append("Kriter listesi okunamadı")
    return {
        "kind": "DOCUMENT_CONSISTENCY_NOT_COMPLIANCE",
        "markdown_files": len(docs),
        "criteria": 8,
        "passed": not errors,
        "errors": errors,
    }


def main():
    """CI için JSON özeti yaz; bozuk belge/kanıtta sıfır olmayan kodla dur."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = check(Path(__file__).resolve().parents[1])
    encoded = json.dumps(result, ensure_ascii=False, indent=2)
    print(encoded)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded + "\n", encoding="utf-8")
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
