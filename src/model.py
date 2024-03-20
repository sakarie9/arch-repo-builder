from dataclasses import dataclass
from enum import Enum, unique


@unique
class ResultEnum(Enum):
    OK = "Build and Copyed"
    COPY = "Skip Build but Copyed"
    SKIP = "Skipped"
    FAIL = "Failed"


@dataclass
class BuildResult:
    pkgname: str
    result: str

    def __str__(self) -> str:
        return f"{self.pkgname}\t{self.result}"
