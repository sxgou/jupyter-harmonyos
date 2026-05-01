"""Sugar layer for zmq (compatibility shim).

This submodule is imported when zmq is imported, providing
the zmq.sugar.socket.Socket reference used by jupyter_client.
"""
from zmq import Socket  # noqa: F401
from zmq import Context  # noqa: F401
