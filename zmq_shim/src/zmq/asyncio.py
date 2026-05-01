"""AsyncIO integration for ZMQ.

Provides AsyncIOContext and AsyncIOSocket for use with asyncio.
The socket methods remain synchronous (matching pyzmq behavior where
the caller uses run_in_executor for true async I/O).
"""
import asyncio
from functools import partial

from zmq import (
    Context as SyncContext,
    Socket as SyncSocket,
    ZMQError,
)


class AsyncIOSocket(SyncSocket):
    """AsyncIO-compatible ZMQ socket.

    Socket methods remain synchronous. For truly async I/O, callers
    should use run_in_executor or the asyncio event loop.
    """
    async def send(self, data, flags=0):
        """Send data asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(super().send, data, flags))

    async def recv(self, flags=0, copy=True, track=False):
        """Receive data asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(super().recv, flags, copy, track))

    async def send_multipart(self, msg_parts, flags=0, copy=True, track=False):
        """Send multipart message asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(super().send_multipart, msg_parts, flags, copy, track)
        )

    async def recv_multipart(self, flags=0, copy=True, track=False):
        """Receive multipart message asynchronously."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None, partial(super().recv_multipart, flags, copy, track)
        )

    def fileno(self):
        """Return the socket's file descriptor (for IOLoop registration)."""
        return self.getsockopt(14)  # ZMQ_FD = 14


class AsyncIOContext(SyncContext):
    """AsyncIO-compatible ZMQ context."""

    _instance = None

    def socket(self, socket_type, **kwargs):
        sock = super().socket(socket_type, **kwargs)
        async_sock = AsyncIOSocket.__new__(AsyncIOSocket)
        async_sock._handle = sock._handle
        async_sock._type = sock._type
        async_sock._context = sock._context
        async_sock._closed = sock._closed
        return async_sock


# Alias for pyzmq compatibility
Context = AsyncIOContext
Socket = AsyncIOSocket
