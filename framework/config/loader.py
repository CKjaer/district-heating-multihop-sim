from pathlib import Path

import yaml
from dacite import from_dict

from .models import Config


def load_config(path: Path = Path("configuration.yml")) -> Config:
    """Load the configuration from yaml file to a Config object"""
    with path.open() as file:
        data = yaml.safe_load(file)
    return from_dict(Config, data)