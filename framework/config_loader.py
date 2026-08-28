from dataclasses import dataclass
from pathlib import Path

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[1] / "configuration.yml"


@dataclass
class Settings:
    burial_depth: float
    num_nodes: int
    spacing: float


def load_config(path: Path = _CONFIG_PATH) -> Settings:
    with path.open() as file:
        settings = Settings(**yaml.safe_load(file))

    return settings


settings = load_config()

if __name__ == "__main__":
    print(settings)
