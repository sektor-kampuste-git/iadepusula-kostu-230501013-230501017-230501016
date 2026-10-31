"""Reproduce the curated snapshot from the locally downloaded official sources.

Input: .local/ministry-book.txt, ministry-book.pdf, ministry-distance.txt/html.
This is an importer, not an automatic legal update. Review sources before replacing data.
The 2023 book is used ONLY for selected unchanged provisions; current guidance is separate.
"""

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / ".local"
OUTPUT = ROOT / "data" / "mevzuat_derlemi"
BOOK_URL = (
    "https://tuketici.ticaret.gov.tr/data/5e81982d13b876a1b04c7a42/"
    "2023-6502%20Say%C4%B1l%C4%B1%20T%C3%BCketicinin%20Korunmas%C4%B1%20"
    "Hakk%C4%B1nda%20Kanun.pdf"
)
GUIDE_URL = (
    "https://tuketici.ticaret.gov.tr/yayinlar/tuketici-bilgi-rehberi/"
    "mesafeli-sozlesmeler-hakkinda-bilgilendirme"
)


def clean(text):
    text = re.sub(r"--- PDF PAGE \d+ ---", "", text)
    text = re.sub(r"-\s+\d+\s+-", "", text)
    for header in [
        "Tüketicinin Korunması Hakkında Kanun",
        "Mesafeli Sözleşmeler Yönetmeliği",
        "Yönetmelikler",
    ]:
        text = text.replace(header, "")
    text = re.sub(r"\((?:Ek ibare|Değişik ibare|Değişik|Ek cümle|Ek):[^)]*\)(?:\(\d+\))?", "", text)
    text = re.sub(r"(?<=[.;])\(\d+\)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def build():
    book = (SOURCE / "ministry-book.txt").read_text(encoding="utf-8")
    book_hash = hashlib.sha256((SOURCE / "ministry-book.pdf").read_bytes()).hexdigest()
    guide = (SOURCE / "ministry-distance.txt").read_text(encoding="utf-8")
    guide_hash = hashlib.sha256((SOURCE / "ministry-distance.html").read_bytes()).hexdigest()
    chunks = []

    def add(
        cid,
        doc,
        kind,
        title,
        article,
        heading,
        text,
        keywords=(),
        url=BOOK_URL,
        digest=book_hash,
        context=None,
    ):
        chunks.append(
            {
                "chunk_id": cid,
                "belge_id": doc,
                "kaynak_turu": kind,
                "belge_basligi": title,
                "madde": article,
                "baslik": heading,
                "metin": clean(text),
                "kaynak_url": url,
                "erisim_tarihi": "2026-10-31",
                "gecerli_baslangic": "2026-01-01",
                "gecerli_bitis": None,
                "anahtar_kelimeler": list(keywords),
                "kaynak_sha256": digest,
                "baglam": context,
            }
        )

    law = book[book.index("Ayıplı mal\nMADDE 8") : book.index("Ayıplı hizmet\nMADDE 13")]
    law = law.split("İKİNCİ BÖLÜM")[0]
    law_titles = {
        8: "Ayıplı mal",
        9: "Ayıplı maldan sorumluluk",
        10: "İspat yükü",
        11: "Tüketicinin seçimlik hakları",
        12: "Zamanaşımı",
    }
    # Locate article boundaries structurally, preserving paragraphs and their references.
    starts = list(re.finditer(r"MADDE (\d+)\s*[-–]", law))
    for pos, match in enumerate(starts):
        number = int(match[1])
        body = law[match.end() : starts[pos + 1].start() if pos + 1 < len(starts) else len(law)]
        if pos + 1 < len(starts):
            body = body[: body.rfind(law_titles[number + 1])]
        paragraphs = list(re.finditer(r"(?:^|\n)\s*\((\d+)\)\s*", body))
        for index, paragraph in enumerate(paragraphs):
            num = paragraph[1]
            text = body[
                paragraph.end() : paragraphs[index + 1].start()
                if index + 1 < len(paragraphs)
                else len(body)
            ]
            keywords = {
                8: ("bozuk", "kusurlu", "arızalı", "çalışmıyor", "kırık", "ayıplı mal"),
                9: ("satıcı sorumluluğu", "sözleşmeye uygun teslim"),
                10: ("ispat", "altı ay", "ayıptan haberdar"),
                11: ("iade", "onarım", "değişim", "bedel indirimi", "seçimlik hak"),
                12: ("iki yıl", "zamanaşımı", "ikinci el", "hile"),
            }[number]
            add(
                f"6502-M{number}-F{num}",
                "6502",
                "kanun",
                "6502 sayılı Tüketicinin Korunması Hakkında Kanun",
                f"Madde {number}/{num}",
                law_titles[number],
                text,
                keywords,
            )

    start = book.index("Cayma hakkı\nMADDE 9")
    end = book.index("Sözleşmenin ifası ve teslimat", start)
    distance = book[start:end]

    def article_body(number, next_heading):
        m = re.search(rf"MADDE {number}\s*[-–]", distance)
        return distance[m.end() : distance.index(next_heading, m.end())]

    selections = [
        (
            9,
            "Eksik bilgilendirme",
            "Cayma hakkı",
            ("cayma", "14 gün", "teslim", "parçalı teslim"),
            None,
        ),
        (10, "Cayma hakkının kullanımı", "Eksik bilgilendirme", ("bilgilendirme", "bir yıl"), None),
        (
            11,
            "Satıcı veya sağlayıcının yükümlülükleri",
            "Cayma bildirimi",
            ("bildirim", "kalıcı veri saklayıcısı"),
            {"1", "4"},
        ),
    ]
    for number, next_heading, heading, keywords, keep in selections:
        body = article_body(number, next_heading)
        paragraphs = list(re.finditer(r"(?:^|\n)\s*\((\d+)\)\s*", body))
        for index, paragraph in enumerate(paragraphs):
            num = paragraph[1]
            if keep is not None and num not in keep:
                continue
            text = body[
                paragraph.end() : paragraphs[index + 1].start()
                if index + 1 < len(paragraphs)
                else len(body)
            ]
            add(
                f"MSY-M{number}-F{num}",
                "MSY",
                "yonetmelik",
                "Mesafeli Sözleşmeler Yönetmeliği",
                f"Madde {number}/{num}",
                heading,
                text,
                keywords,
            )

    body = distance[distance.index("MADDE 15") :]
    matches = list(re.finditer(r"(?:^|\n)([abcçde fgğhıijk])\)\s*", body))
    for index, match in enumerate(matches):
        letter = match[1]
        if letter in "ıijk":
            continue  # Do NOT import the obsolete 2023 electronic-product exemption.
        text = body[
            match.end() : matches[index + 1].start() if index + 1 < len(matches) else len(body)
        ]
        keywords = {
            "a": ("finansal dalgalanma", "altın"),
            "b": ("kişiye özel", "kişiselleştirme", "isim baskı"),
            "c": ("çabuk bozulma", "gıda", "yaş pasta"),
            "ç": ("hijyen", "mühür", "ambalaj"),
            "d": ("karışan ürün",),
            "e": ("kitap", "kartuş", "dijital içerik"),
            "f": ("gazete", "dergi"),
            "g": ("otel", "rezervasyon", "konaklama"),
            "ğ": ("anında ifa", "dijital"),
            "h": ("hizmet", "onay"),
        }[letter]
        add(
            f"MSY-M15-{letter}",
            "MSY",
            "yonetmelik",
            "Mesafeli Sözleşmeler Yönetmeliği",
            f"Madde 15/1-{letter}",
            "Cayma hakkı istisnası — " + keywords[0],
            text,
            keywords,
            context="Taraflarca aksi kararlaştırılmadıkça, tüketici aşağıdaki sözleşmelerde cayma hakkını kullanamaz:",
        )

    # The updated 2026 guide is explicitly labelled as guidance, never as statutory text.
    excerpts = [
        (
            "REHBER-ELEKTRONIK",
            "Elektronik ürünler",
            "Anılan ürünler cayma hakkının istisnası kapsamında olmayıp",
            None,
            ("cep telefonu", "tablet", "bilgisayar", "akıllı saat"),
        ),
        (
            "REHBER-KARGO",
            "İade kargo masrafı",
            "Tüketicinin malı ön bilgilendirmede belirtilen kargo şirketi",
            "Kredi kartı kullanılarak",
            ("iade kargo", "masraf"),
        ),
        (
            "REHBER-IADE-SURE",
            "Bedel iadesi ve geri gönderme süresi",
            "Tüketici cayma hakkını kullandığında satıcı/sağlayıcı",
            "Mesafeli sözleşmelerde cayma hakkının kullanılması durumunda kargo",
            ("bedel iadesi", "kargoya teslim", "14 gün", "geri gönderme"),
        ),
        (
            "REHBER-HASAR",
            "Taşımada hasar",
            "Satıcı, ön bilgilendirmede belirtilen kargo vasıtasıyla",
            "Mesafeli sözleşme yöntemiyle yapılan",
            ("kargo", "kırık", "hasar", "teslim"),
        ),
    ]
    for cid, heading, begin, end_marker, keywords in excerpts:
        i = guide.index(begin)
        j = guide.index(end_marker, i) if end_marker else len(guide)
        add(
            cid,
            "TICARET-REHBER-2026",
            "resmi_rehber",
            "Ticaret Bakanlığı Mesafeli Sözleşmeler Bilgilendirmesi",
            "Rehber: " + heading,
            heading,
            guide[i:j],
            keywords,
            GUIDE_URL,
            guide_hash,
        )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    for filename, records in [
        ("6502.json", [c for c in chunks if c["belge_id"] == "6502"]),
        ("mesafeli_sozlesmeler.json", [c for c in chunks if c["belge_id"] == "MSY"]),
        ("ticaret_rehberi_2026.json", [c for c in chunks if c["kaynak_turu"] == "resmi_rehber"]),
    ]:
        (OUTPUT / filename).write_text(
            json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    print(f"Imported {len(chunks)} traceable excerpts. Legal expert sign-off remains pending.")


if __name__ == "__main__":
    build()
