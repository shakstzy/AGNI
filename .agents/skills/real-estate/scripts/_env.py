"""Load KEY=value lines from the skill's .env into os.environ (no overwrite).

Lets optional credentials (CENSUS_API_KEY, HUD_API_TOKEN) live in a gitignored
.env in the skill folder -- the CORTANA convention for self-contained skills --
and be picked up no matter how `re` is invoked (direct CLI or via the pipeline
subprocess). Call `ensure_loaded()` before reading those env vars.
"""

import os

_ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
_loaded = False


def ensure_loaded() -> None:
    global _loaded
    if _loaded:
        return
    _loaded = True
    try:
        with open(_ENV_PATH) as f:
            for raw in f:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except OSError:
        pass
