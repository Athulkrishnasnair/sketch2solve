"""Immutable, normalized data structures for planar truss input."""

from dataclasses import dataclass
from typing import Literal


SupportType = Literal["pin", "roller"]
SupportDirection = Literal["horizontal", "vertical"]


@dataclass(frozen=True)
class Units:
    length: Literal["m", "mm", "ft"]
    force: Literal["N", "kN", "lbf"]


@dataclass(frozen=True)
class Node:
    id: str
    x: float
    y: float


@dataclass(frozen=True)
class Member:
    id: str
    node_i: str
    node_j: str


@dataclass(frozen=True)
class Support:
    id: str
    node: str
    type: SupportType
    direction: SupportDirection | None = None


@dataclass(frozen=True)
class Load:
    id: str
    node: str
    fx: float
    fy: float


@dataclass(frozen=True)
class TrussModel:
    schema_version: str
    name: str | None
    source: str | None
    units: Units
    nodes: tuple[Node, ...]
    members: tuple[Member, ...]
    supports: tuple[Support, ...]
    loads: tuple[Load, ...]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    path: str
    message: str


@dataclass(frozen=True)
class ValidationResult:
    model: TrussModel | None
    errors: tuple[ValidationIssue, ...]

    @property
    def is_valid(self) -> bool:
        return self.model is not None and not self.errors
