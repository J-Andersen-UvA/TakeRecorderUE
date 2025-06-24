import yaml
from pathlib import Path
import scripts.utils.popUp as popUp

class Config:
    def __init__(self, config_path: str = None):
        # Point at your YAML (default to scripts/config/config.yaml)
        path = Path(config_path or Path(__file__).parent / "config.yaml")
        if not path.exists():
            popUp.show_popup_message("Configuration Error", f"Config file not found at {path}")
            raise FileNotFoundError(f"Config file not found at {path}")
        with path.open("r") as f:
            data = yaml.safe_load(f)
        self._validate(data)
        self._data = data

    def _validate(self, d: dict):
        required = ["export_endpoint", "ws_url", "record_path"]
        missing = [k for k in required if k not in d]
        if missing:
            popUp.show_popup_message("Configuration Error", f"Missing keys in config.yaml: {', '.join(missing)}")
            raise KeyError(f"Missing keys in config.yaml: {missing}")

    def __getattr__(self, name):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"No config attribute called {name}")
