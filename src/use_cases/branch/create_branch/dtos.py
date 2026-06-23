from dataclasses import dataclass


@dataclass
class CreateBranchInput:
    name: str
    city: str
    uf: str
    address: str


@dataclass
class CreateBranchOutput:
    id: int
    name: str
