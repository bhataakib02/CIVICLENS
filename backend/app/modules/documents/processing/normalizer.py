"""Value normalization (prompt §25).

Each normalizer takes a raw extracted string and returns a NormalizedValue
(raw_value always preserved, normalized_value + value_type + ok flag). Invalid
inputs return ok=False with normalized_value=None (never fabricated, never a
guessed default). Numeric income can never be negative.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from app.models.enums import FieldValueType

_INDIAN_STATES = {
    "west bengal": "WEST_BENGAL", "bihar": "BIHAR", "kerala": "KERALA",
    "karnataka": "KARNATAKA", "maharashtra": "MAHARASHTRA", "tamil nadu": "TAMIL_NADU",
    "uttar pradesh": "UTTAR_PRADESH", "rajasthan": "RAJASTHAN", "gujarat": "GUJARAT",
    "punjab": "PUNJAB", "delhi": "DELHI",
}


@dataclass
class NormalizedValue:
    raw_value: str
    normalized_value: str | None
    value_type: FieldValueType
    ok: bool


def normalize_income(raw: str) -> NormalizedValue:
    s = (raw or "").strip()
    negative = s.startswith("-")
    digits = re.sub(r"[^\d.]", "", s)
    if not digits or digits == ".":
        return NormalizedValue(raw, None, FieldValueType.NUMBER, False)
    try:
        value = float(digits)
    except ValueError:
        return NormalizedValue(raw, None, FieldValueType.NUMBER, False)
    if negative or value < 0:  # income can never be negative
        return NormalizedValue(raw, None, FieldValueType.NUMBER, False)
    # Store as integer rupees when whole.
    norm = str(int(value)) if value.is_integer() else str(value)
    return NormalizedValue(raw, norm, FieldValueType.NUMBER, True)


def normalize_state(raw: str) -> NormalizedValue:
    key = (raw or "").strip().lower()
    mapped = _INDIAN_STATES.get(key)
    if mapped is None:
        return NormalizedValue(raw, None, FieldValueType.STRING, False)
    return NormalizedValue(raw, mapped, FieldValueType.STRING, True)


def normalize_date(raw: str) -> NormalizedValue:
    s = (raw or "").strip()
    patterns = [
        ("%Y-%m-%d", re.compile(r"^\d{4}-\d{2}-\d{2}$")),
        ("%d/%m/%Y", re.compile(r"^\d{2}/\d{2}/\d{4}$")),
        ("%d-%m-%Y", re.compile(r"^\d{2}-\d{2}-\d{4}$")),
    ]
    from datetime import datetime

    for fmt, rx in patterns:
        if rx.match(s):
            try:
                d = datetime.strptime(s, fmt).date()
                if d > date.today():
                    return NormalizedValue(raw, None, FieldValueType.DATE, False)
                return NormalizedValue(raw, d.isoformat(), FieldValueType.DATE, True)
            except ValueError:
                return NormalizedValue(raw, None, FieldValueType.DATE, False)
    return NormalizedValue(raw, None, FieldValueType.DATE, False)


def normalize_postal_code(raw: str) -> NormalizedValue:
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) != 6:
        return NormalizedValue(raw, None, FieldValueType.STRING, False)
    return NormalizedValue(raw, digits, FieldValueType.STRING, True)


def normalize_text(raw: str) -> NormalizedValue:
    s = " ".join((raw or "").split())
    if not s:
        return NormalizedValue(raw, None, FieldValueType.STRING, False)
    return NormalizedValue(raw, s, FieldValueType.STRING, True)


# field_name -> normalizer
FIELD_NORMALIZERS = {
    "annual_income": normalize_income,
    "state": normalize_state,
    "date_of_birth": normalize_date,
    "issue_date": normalize_date,
    "postal_code": normalize_postal_code,
    "district": normalize_text,
    "person_name": normalize_text,
    "issuing_authority": normalize_text,
    "certificate_number": normalize_text,
    "financial_year": normalize_text,
}


def normalize_field(field_name: str, raw: str) -> NormalizedValue:
    fn = FIELD_NORMALIZERS.get(field_name, normalize_text)
    return fn(raw)
