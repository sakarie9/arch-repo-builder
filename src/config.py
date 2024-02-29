import yaml
import os
from dataclasses import dataclass, field
from typing import List

BASE_PATH = os.getcwd()
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
        except FileNotFoundError:
            print("!!!config.yaml not exist!")
            raise
        except:
            f.close()
            raise

        try:
            self.global_settings = GlobalSettings(**config["global-settings"])
        except (KeyError) as err:
            self.global_settings = GlobalSettings()

        try:
            self.pkgbuilds = Pkgbuilds(**config["pkgbuilds"])
        except (KeyError) as err:
            self.pkgbuilds = Pkgbuilds()

        try:
            self.aurs = AURs(**config["aurs"])
        except (KeyError) as err:
            self.aurs = AURs()

    def __repr__(self) -> str:
        return f"{self.global_settings}\n{self.pkgbuilds}\n{self.aurs}"

# global config
C = Config()