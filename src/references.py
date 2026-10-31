"""Resolve explicit Turkish legal references before evidence ranking.

An article number alone does not identify a legal instrument. Preserve Turkish
subparagraph letters: c and ç identify different provisions.
"""

import re
from dataclasses import dataclass

from src.privacy import normalize_input

_DOCUMENTS = {
    "6502": r"\b(?:6502|tkhk|tuketicinin korunmasi(?: hakkinda)? kanun\w*)\b",
    "MSY": r"\b(?:msy|mesafeli sozlesmeler yonetmeli\w*)\b",
}
_DETAIL = r"(?P<number>\d+)(?:\s*/\s*(?P<paragraph>\d+))?(?:\s*[-/]\s*(?P<letter>[a-zçğıöşü]))?"
_FORWARD = re.compile(r"\b(?:madde(?:si|sinin|sine|sinde)?|md\.?)\s*" + _DETAIL)
_REVERSE = re.compile(r"\b" + _DETAIL + r"\.?\s*(?:inci|ıncı|uncu|üncü|nci|ncı|ncu|ncü)?\s*madd\w*")


@dataclass(frozen=True)
class ArticleReference:
    document: str | None
    number: int
    paragraph: int | None = None
    letter: str | None = None

    def matches(self, document: str, article: str) -> bool:
        candidate = _FORWARD.search(article.lower())
        if not candidate or (self.document is not None and document != self.document):
            return False
        return (
            int(candidate["number"]) == self.number
            and (
                self.paragraph is None
                or candidate["paragraph"] is not None
                and int(candidate["paragraph"]) == self.paragraph
            )
            and (self.letter is None or candidate["letter"] == self.letter)
        )


def parse_references(query: str) -> tuple[ArticleReference, ...]:
    text = normalize_input(query).replace("İ", "i").lower()
    folded = text.translate(str.maketrans("çğıöşü", "cgiosu"))
    markers = sorted(
        (match.start(), match.end(), doc)
        for doc, pattern in _DOCUMENTS.items()
        for match in re.finditer(pattern, folded)
    )
    matches = sorted([*_FORWARD.finditer(text), *_REVERSE.finditer(text)], key=lambda m: m.start())
    result = []
    previous_end = -1
    for match in matches:
        if any(start <= match.start("number") < end for start, end, _ in markers):
            continue  # A law identifier such as 6502 is not an article number.
        if match.start() < previous_end:
            continue
        previous_end = match.end()
        before = [marker for marker in markers if marker[0] <= match.start()]
        document = before[-1][2] if before else None
        if document is None:
            after = [marker for marker in markers if 0 <= marker[0] - match.end() <= 35]
            if after:
                document = after[0][2]
            elif len({marker[2] for marker in markers}) == 1:
                document = markers[0][2]
        reference = ArticleReference(
            document,
            int(match["number"]),
            int(match["paragraph"]) if match["paragraph"] else None,
            match["letter"],
        )
        if reference not in result:
            result.append(reference)
    return tuple(result)
