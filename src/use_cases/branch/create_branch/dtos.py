from dataclasses import dataclass


@dataclass
class CreateBranchInput:
    name: str
    industry_id: str


@dataclass
class CreateBranchOutput:
    id: str
    name: str
