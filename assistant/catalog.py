"""Service catalogue: the only source of truth for what the assistant may offer."""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Service:
    code: str
    name: str
    price_from: int
    duration_min: int


class Catalog:
    def __init__(self, services: list[Service], unsupported_vehicles: list[str], working_hours: str):
        self.services = services
        self.unsupported_vehicles = [v.lower() for v in unsupported_vehicles]
        self.working_hours = working_hours

    @classmethod
    def load(cls, path: str | Path) -> "Catalog":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls(
            [Service(**s) for s in data["services"]],
            data.get("unsupported_vehicles", []),
            data.get("working_hours", ""),
        )

    def by_code(self, code: str) -> Service | None:
        return next((s for s in self.services if s.code == code), None)

    def is_vehicle_supported(self, car: str) -> bool:
        car = car.lower()
        return not any(word in car for word in self.unsupported_vehicles)

    def as_prompt(self) -> str:
        lines = [f"- {s.code}: {s.name}, from {s.price_from} RUB, ~{s.duration_min} min" for s in self.services]
        return (
            "Services (the ONLY ones you may offer):\n" + "\n".join(lines)
            + f"\nNot serviced: {', '.join(self.unsupported_vehicles) or 'none'}"
            + f"\nWorking hours: {self.working_hours}"
        )
