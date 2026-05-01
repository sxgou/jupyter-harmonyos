"""SSH tunneling utilities for ZMQ (stub).

On HarmonyOS, SSH tunneling is not supported in this shim.
"""
import warnings


def tunnel_to_kernel(connection_info, sshserver, sshkey=None):
    """Stub: SSH tunneling is not supported."""
    warnings.warn("SSH tunneling is not supported in zmq-shim", RuntimeWarning)
    return connection_info


def tunnel_to_kernel_tcp(ip, port, ssh, keyfile, paramiko=False):
    """Stub: SSH TCP tunneling."""
    raise NotImplementedError("SSH tunneling not supported in zmq-shim")


def tunnel_to_kernel_ws(ip, port, ssh, keyfile, paramiko=False):
    """Stub: SSH WebSocket tunneling."""
    raise NotImplementedError("SSH tunneling not supported in zmq-shim")
