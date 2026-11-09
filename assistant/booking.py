"""Booking draft: collects only the fields needed to book a visit."""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict

REQUIRED = ("service", "name", "phone", "car", "time")


def normalize_phone(raw: str) -> str | None:
    """Return a Russian mobile number as +7XXXXXXXXXX, or None if it is not valid."""
    digits = re.sub(r"\D", "", raw or "")
    if len(digits) == 11 and digits[0] in "78":
        digits = "7" + digits[1:]
    elif len(digits) == 10 and digits[0] == "9":
        digits = "7" + digits
    else:
        return None
    return "+" + digits if digits[1] == "9" else None


@dataclass
class BookingDraft:
    service: str | None = None
    name: str | None = None
    phone: str | None = None
    car: str | None = None
    time: str | None = None
    notes: list[str] = field(default_factory=list)

    def update(self, fields: dict) -> list[str]:
        """Merge fields extracted by the model. Returns a list of validation problems."""
        problems = []
        for key in REQUIRED:
            value = (fields or {}).get(key)
            if not value:
                continue
            if key == "phone":
                phone = normalize_phone(str(value))
                if phone is None:
                    problems.append("phone")
                    continue
                value = phone
            setattr(self, key, str(value).strip()[:80])
        return problems

    def missing(self) -> list[str]:
        return [k for k in REQUIRED if not getattr(self, k)]

    def is_complete(self) -> bool:
        return not self.missing()

    def to_dict(self) -> dict:
        return asdict(self)
