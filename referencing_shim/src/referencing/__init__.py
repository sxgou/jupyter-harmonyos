"""Stub shim for referencing - pure Python without rpds-py.

Provides the minimal API surface needed by jupyter_events.
Also monkey-patches jsonschema.Draft7Validator to accept registry keyword
and inject registry resources into RefResolver.
"""
from typing import Any
import jsonschema
import inspect


# ── Resource ──────────────────────────────────────────────────────────────

class Resource:
    """A JSON Schema resource."""
    def __init__(self, contents, specification=None):
        self.contents = contents
        self.specification = specification

    def __or__(self, registry):
        """Operator | or @ to add this resource to a registry."""
        if isinstance(registry, Registry):
            registry = registry._add(self)
        return registry


# ── Registry ──────────────────────────────────────────────────────────────

class Registry:
    """A registry of JSON Schema resources."""
    def __init__(self, resources=None):
        self._resources = {}
        if resources:
            for r in resources:
                self._resources[self._uri(r)] = r

    @staticmethod
    def _uri(resource):
        """Extract $id from a Resource's contents."""
        return resource.contents.get("$id", "")

    def _add(self, resource):
        uri = self._uri(resource)
        if uri:
            self._resources[uri] = resource
        return self

    def __or__(self, other):
        if isinstance(other, Registry):
            merged = dict(self._resources)
            merged.update(other._resources)
            return Registry(list(merged.values()))
        return self

    def __ror__(self, other):
        if isinstance(other, Resource):
            return self._add(other)
        if isinstance(other, list):
            for r in other:
                self._add(r)
            return self
        return self

    def __matmul__(self, other):
        return self.__or__(other) if isinstance(other, Registry) else self

    def __rmatmul__(self, other):
        if isinstance(other, Resource):
            return self._add(other)
        if isinstance(other, list):
            for r in other:
                self._add(r)
            return self
        return self

    def get(self, uri):
        """Retrieve a resource by its $id URI."""
        return self._resources.get(uri)

    def __getitem__(self, uri):
        return self._resources[uri]

    def __contains__(self, uri):
        return uri in self._resources


# ── Specification ─────────────────────────────────────────────────────────

class Specification:
    """A JSON Schema specification (e.g., DRAFT7)."""
    def __init__(self, name):
        self.name = name

    def create_resource(self, contents):
        """Create a Resource from schema contents."""
        return Resource(contents, specification=self)


# ── Monkey-patch jsonschema for registry compat ──────────────────────────

def _patch_draft7():
    """Patch Draft7Validator to accept and use the `registry` kwarg."""
    try:
        cls = jsonschema.Draft7Validator
        sig = inspect.signature(cls.__init__)

        orig_init = cls.__init__
        using_old_api = 'registry' not in sig.parameters

        def _patched_init(self, schema, registry=None, **kwargs):
            if using_old_api:
                orig_init(self, schema, **kwargs)
            else:
                orig_init(self, schema, registry=registry, **kwargs)

            # Inject registry resources into the RefResolver's store
            # so $ref/ URI resolution works without HTTP fetches.
            if registry is not None and hasattr(self, 'resolver'):
                for uri, resource in registry._resources.items():
                    if uri and uri not in self.resolver.store:
                        self.resolver.store[uri] = resource.contents

        cls.__init__ = _patched_init
    except Exception:
        pass  # fail silently


_patch_draft7()
