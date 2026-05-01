"""Sugar socket wrapper (compatibility shim).

Re-exports the Socket class from the zmq core module.
"""
from zmq import Socket  # noqa: F401
