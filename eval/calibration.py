"""Compute agreement from actual review records; never invent human labels."""

import argparse
import json
from collections import Counter
from pathlib import Path

from pydantic import Field, StrictInt, field_validator

from src.contracts import Contract


class ReviewRecord(Contract):
    id: str = Field(min_length=1)
    reviewer: str = Field(min_length=1)
    human_score: StrictInt = Field(ge=0, le=1)
    judge_score: StrictInt = Field(ge=0, le=1)

    @field_validator("id", "reviewer")
    @classmethod
    def nonempty_text(cls, value):
        if not value.strip():
            raise ValueError("Gerçek insan/hakem skoru ve etiketleyen bilgisi gereklidir")
        return value.strip()


def calibration(records: list[dict]) -> dict:
    try:
        records = [ReviewRecord.model_validate(row).model_dump() for row in records]
    except ValueError:
        raise ValueError("Gerçek insan/hakem skoru ve etiketleyen bilgisi gereklidir") from None
    ids = [row["id"] for row in records]
    if len(ids) != len(set(ids)):
        raise ValueError("Kalibrasyon kimlikleri tekrarlanamaz")
    for row in records:
        if (
            row.get("human_score") not in (0, 1)
            or row.get("judge_score") not in (0, 1)
            or not row.get("reviewer")
        ):
            raise ValueError("Gerçek insan/hakem skoru ve etiketleyen bilgisi gereklidir")
    if len(records) < 10:
        raise ValueError("Kalibrasyon için en az 10 gerçek insan değerlendirmesi gerekir")
    n = len(records)
    human = Counter(row["human_score"] for row in records)
    judge = Counter(row["judge_score"] for row in records)
    agreement = sum(row["human_score"] == row["judge_score"] for row in records) / n
    expected = sum(human[value] * judge[value] for value in (0, 1)) / (n * n)
    return {
        "n": n,
        "agreement": agreement,
        "cohens_kappa": (agreement - expected) / (1 - expected) if expected < 1 else None,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("reviews", type=Path)
    args = parser.parse_args()
    records = [
        json.loads(line)
        for line in args.reviews.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    print(json.dumps(calibration(records), indent=2))
