"""Bounded JSON transport decoding; does not authenticate a sender."""
import json
from pathlib import Path

MAX_DOSSIER_BYTES = 128 * 1024


def _unique_fields(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("Duplicate dossier field")
        value[key] = item
    return value


def read_dossier(path):
    with Path(path).open("rb") as stream:
        raw = stream.read(MAX_DOSSIER_BYTES + 1)
    if len(raw) > MAX_DOSSIER_BYTES:
        raise ValueError("Dossier exceeds size limit")
    return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_fields,
                      parse_constant=lambda _: (_ for _ in ()).throw(ValueError("Nonfinite JSON value")))
