"""Small local boundary for Member 1 demos, not a complete KVKK compliance system.

Names and addresses cannot reliably be found by these patterns. Do not send real
applications to the provider before Member 2 integrates the full security layer.
"""

import re
import unicodedata

PATTERNS = (
    ("IBAN", re.compile(r"\bTR\s*\d{2}(?:\s*\d){22}\b", re.I)),
    ("EPOSTA", re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")),
    (
        "TELEFON",
        re.compile(
            r"(?<!\d)(?:\+?90[\s().-]*)?0?\(?[2-589]\d{2}\)?[\s.-]*\d{3}[\s.-]*\d{2}[\s.-]*\d{2}(?!\d)"
        ),
    ),
    ("TCKN", re.compile(r"(?<!\d)[1-9](?:[ .-]?\d){10}(?!\d)")),
)


def normalize_input(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    return "".join(c for c in text if unicodedata.category(c) != "Cf")


def mask_pii(text: str) -> str:
    result = normalize_input(text)
    for label, pattern in PATTERNS:
        result = pattern.sub(f"<{label}_MASKELENDI>", result)
    return result


def retrieval_query(masked_text: str) -> str:
    """Remove masked identifier fields so labels do not distort evidence retrieval."""
    result = re.sub(
        r"\b(?:TCKN|IBAN|telefon|e-posta|e-posta adresi)\s*:?\s*<[A-Z]+_MASKELENDI>",
        " ",
        masked_text,
        flags=re.I,
    )
    return re.sub(r"<[A-Z]+_MASKELENDI>", " ", result)


def obvious_injection(text: str) -> bool:
    text = normalize_input(text).lower().replace("ı", "i")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    patterns = (
        r"(?:onceki|tum|butun).{0,35}(?:yonerge|talimat|kural).{0,25}(?:unut|yok say|ignore)",
        r"ignore.{0,30}(?:previous|instructions|rules)",
        r"\[\s*system\s*:",
        r"<\s*/?\s*system\s*>",
        r"(?:sistem|system)\s*(?:prompt|istem).{0,25}(?:goster|yaz|acikla|reveal)",
        r"(?:api[ _-]*key|api anahtar\w*).{0,30}(?:goster|ver|yaz|print|reveal)",
        r"(?:tum|diger|butun).{0,25}(?:musteri|siparis).{0,30}(?:listele|kimlik|iban|telefon)",
    )
    return any(re.search(pattern, text, re.S) for pattern in patterns)


def outside_scope(text: str) -> bool:
    """Recognize a few explicit unrelated tasks without substring word collisions."""
    text = normalize_input(text).lower().replace("ı", "i")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    patterns = (
        r"\bise\s+iade\b",
        r"\bbosanma\w*\b",
        r"\bceza\s+dava\w*\b",
        r"\bmaas\s+tablo\w*\b",
        r"\bkripto(?:\s+para)?\b.{0,50}\b(?:alim.satim|al.sat|ticaret bot\w*|botu|sinyal\w*)\b",
    )
    return any(re.search(pattern, text) for pattern in patterns)
