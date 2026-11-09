"""Credentials for scripts: the shipped defaults overlaid by the user's own file. Stdlib only.

    from creds import get
    get("backoffice", "user")

Order: DATA/credentials/local.json  ({"v":1,"values":{"group.key": "..."}}; an empty string means "use the default")
       then HOME/data/credentials/defaults.json (same shape). Missing file = empty. The values never go to a log:
the CLI prints names and whether each is set, never a value; `get` is for code.

    python -X utf8 creds.py            # group.key  set|default|missing
"""
import json, os, pathlib, sys

HOME = pathlib.Path(os.environ.get("NJQA_HOME") or pathlib.Path(__file__).resolve().parents[3])
DATA = pathlib.Path(os.environ.get("NJQA_DATA") or (pathlib.Path(os.environ.get("USERPROFILE") or pathlib.Path.home()) / "NJ-QA-data"))


def _values(path):
    try:
        v = json.loads(pathlib.Path(path).read_text(encoding="utf-8")).get("values")
        return v if isinstance(v, dict) else {}
    except (OSError, ValueError):
        return {}


def _layers():
    defaults = {} if os.environ.get("NJQA_NO_DEFAULT_CREDS") else _values(HOME / "data" / "credentials" / "defaults.json")
    return defaults, _values(DATA / "credentials" / "local.json")


def get(group, key, fallback=""):
    defaults, local = _layers()
    name = f"{group}.{key}"
    return local.get(name) or defaults.get(name) or fallback


def schema():
    p = HOME / "mcp" / "lib" / "creds-schema.json"
    return json.loads(p.read_text(encoding="utf-8")).get("fields", [])


def main():
    defaults, local = _layers()
    for f in schema():
        name = f"{f['group']}.{f['key']}"
        state = "set" if local.get(name) else "default" if defaults.get(name) else "missing"
        print(f"{name}\t{state}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
