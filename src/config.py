import os
import sys
from dataclasses import dataclass, field
from typing import List

import yaml

BASE_PATH = sys.argv[1] if (len(sys.argv) - 1) else os.getcwd()
CONFIG_PATH = os.path.join(BASE_PATH, "config.yaml")


@dataclass
class GlobalSettings:
    repository: str = "repo/repo.db.tar.gz"
    packager: str = "Bob <bob@example.com>"


@dataclass
class Pkgbuilds:
    container: str = "pkgbuilds"


@dataclass
class AURs:
    container: str = "aurs"
    packages: List[str] = field(default_factory=list)


class Config:
    global_settings: GlobalSettings
    pkgbuilds: Pkgbuilds
    aurs: AURs

    def __init__(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                f.close()
        except FileNotFoundError:
            print("!!!config.yaml not exist!")
            raise
        except:
            raise

        try:
            self.global_settings = GlobalSettings(**config["global-settings"])
        except KeyError:
            self.global_settings = GlobalSettings()

        try:
            self.pkgbuilds = Pkgbuilds(**config["pkgbuilds"])
        except KeyError:
            self.pkgbuilds = Pkgbuilds()

        try:
            self.aurs = AURs(**config["aurs"])
        except KeyError:
            self.aurs = AURs()

    def __repr__(self) -> str:
        return f"{self.global_settings}\n{self.pkgbuilds}\n{self.aurs}"


# global config
C = Config()
