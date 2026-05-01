"""Minimal jsonapi shim for ipykernel compatibility.

Provides the jsonapi module expected by ipykernel.debugger.
"""
import json
from functools import partial

dumps = json.dumps
loads = json.loads

def dumps_default_separators(obj, **kwargs):
    """Serialize with compact separators."""
    return json.dumps(obj, separators=(',', ':'), **kwargs)
