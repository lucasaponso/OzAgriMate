"""Farm management domain. This service is the authoritative owner of farm records (ADR 07)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Region(str, Enum):
    """Australian states and territories."""

    ACT = "ACT"
    NSW = "NSW"
    NT = "NT"
    QLD = "QLD"
    SA = "SA"
    TAS = "TAS"
    VIC = "VIC"
    WA = "WA"


@dataclass
class Farm:
    id: str
    name: str
    region: Region
