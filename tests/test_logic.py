from pathlib import Path

import pytest

from assistant.booking import BookingDraft, normalize_phone
from assistant.catalog import Catalog
from assistant.llm import parse_answer

CATALOG = Catalog.load(Path(__file__).parent.parent / "services.example.json")


@pytest.mark.parametrize("raw,expected", [
    ("+7 900 123-45-67", "+79001234567"),
    ("89001234567", "+79001234567"),
    ("9001234567", "+79001234567"),
    ("12345", None),
    ("+7 843 233-71-22", None),   # landline is not accepted for SMS confirmation
])
def test_normalize_phone(raw, expected):
    assert normalize_phone(raw) == expected


def test_booking_collects_fields_step_by_step():
    d = BookingDraft()
    d.update({"service": "oil", "name": "Ivan"})
    assert d.missing() == ["phone", "car", "time"]
    assert d.update({"phone": "bad"}) == ["phone"]
    d.update({"phone": "8 900 111 22 33", "car": "Kia Rio", "time": "tomorrow 10:00"})
    assert d.is_complete() and d.phone == "+79001112233"


def test_catalog_rules():
    assert CATALOG.by_code("oil").price_from == 1500
    assert CATALOG.by_code("teleport") is None
    assert not CATALOG.is_vehicle_supported("Toyota Land Cruiser 200")
    assert CATALOG.is_vehicle_supported("Hyundai Solaris")


def test_parse_answer_accepts_valid_json():
    r = parse_answer('{"reply":"Hi","intent":"info","booking":{}}')
    assert r["intent"] == "info" and r["reply"] == "Hi"


@pytest.mark.parametrize("raw", ["", "not json", '{"intent":"hack","reply":"x"}', '{"intent":"info"}'])
def test_parse_answer_falls_back_to_escalation(raw):
    assert parse_answer(raw)["intent"] == "escalate"
