"""ZMQStream - ZMQ socket integration with tornado IOLoop."""
from collections import deque
from tornado.ioloop import IOLoop
from zmq import Socket as _SyncSocket
import zmq
import traceback as _tb
import asyncio as _asyncio
import inspect as _inspect

_POLL_INTERVAL = 50  # ms

_DEBUG = False
import os as _os
import threading as _threading
_DEBUG_FILE = open(_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_debug.log', 'a', buffering=1)
import atexit as _atexit
_atexit.register(_DEBUG_FILE.close)

def _log(msg):
    import sys
    _DEBUG_FILE.write(f'[{_threading.current_thread().name}] {msg}\n')
    _DEBUG_FILE.flush()
    # Use __stderr__ to bypass OutStream (which may block after init_io)
    try:
        if hasattr(sys.stderr, '_original_stdstream_copy'):
            print(f'[ZMQStream] {msg}', file=sys.__stderr__, flush=True)
        else:
            print(f'[ZMQStream] {msg}', file=sys.stderr, flush=True)
    except Exception:
        pass


def _call_cb(cb, msg, loop=None):
    """Call callback, scheduling coroutine/awaitable return values."""
    result = cb(msg)
    if _inspect.isawaitable(result):
        if loop is not None and loop.is_running():
            _asyncio.run_coroutine_threadsafe(result, loop)
        elif loop is not None:
            loop.call_soon(lambda: _asyncio.ensure_future(result))
        else:
            try:
                _asyncio.ensure_future(result)
            except RuntimeError:
                pass


class ZMQStream:
    """A stream wrapper around a ZMQ socket that provides IOLoop integration."""

    def __init__(self, socket, io_loop=None):
        self.socket = socket
        self.io_loop = io_loop or IOLoop.current()
        self._recv_callbacks = []
        self._send_callbacks = []
        self._closed = False
        self._running = False
        self._flushed = False
        self._state = 0
        self._recv_buffer = deque()
        self._poll_count = 0

        if _DEBUG:
            import traceback as _tb
            _tb_file = _os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_init_trace.log'
            with open(_tb_file, 'a') as _f:
                _f.write(f'=== ZMQStream __init__ socket={socket} io_loop={io_loop} type={type(self.io_loop).__name__} ===\n')
                _tb.print_stack(file=_f)
                _f.write('\n')
            _log(f'__init__ socket={socket} io_loop_param={io_loop} '
                 f'io_loop_actual={self.io_loop} type={type(self.io_loop).__name__} '
                 f'thread={threading.current_thread().name}')

        if self.socket:
            import os as _z_os2
            with open(_z_os2.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
                _zf.write(f'__init__ calling _start_polling sock={socket} io_loop={io_loop}\n')
            self._start_polling()
            with open(_z_os2.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf2:
                _zf2.write(f'__init__ _start_polling returned sock={socket}\n')

    def _start_polling(self):
        import os as _z_os
        with open(_z_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
            _zf.write(f'_start_polling ENTERED sock={self.socket}\n')
        if self._closed or self._running:
            with open(_z_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
                _zf.write(f'_start_polling SKIP closed={self._closed} running={self._running}\n')
            return
        self._running = True
        with open(_z_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
            _zf.write(f'_start_polling set _running=True. logging...\n')
        if _DEBUG:
            import asyncio as _aio
            _log(f'_start_polling on thread={threading.current_thread().name} '
                 f'ioloop={self.io_loop} ioloop_thread={getattr(self.io_loop, "_thread_identity", "?")} '
                 f'asyncio_loop={getattr(self.io_loop, "asyncio_loop", "?")} '
                 f'running={getattr(getattr(self.io_loop, "asyncio_loop", None), "_running", "?")}')
        with open(_z_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
            _zf.write(f'_start_polling calling add_callback...\n')
        try:
            self.io_loop.add_callback(self._poll)
        except Exception as _z_e:
            with open(_z_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
                _zf.write(f'_start_polling add_callback FAILED: {_z_e}\n')
            raise
        with open(_z_os.environ.get('HOME', '/tmp') + '/.tmp/zmqstream_trace.log', 'a', buffering=1) as _zf:
            _zf.write('_start_polling add_callback returned OK\n')

    def _poll(self):
        if not self._running or self._closed:
            return
        self._poll_count += 1
        # Log first few polls and every 200th
        if _DEBUG and (self._poll_count <= 5 or self._poll_count % 200 == 0):
            _log(f'_poll #{self._poll_count} on thread={threading.current_thread().name} '
                 f'socket={self.socket} running={self._running} closed={self._closed}')
        try:
            self._handle_recv()
        except Exception as e:
            if _DEBUG:
                _log(f'_poll _handle_recv exception: {e}')
                _tb.print_exc()
        if self._running and not self._closed:
            self.io_loop.add_timeout(
                self.io_loop.time() + _POLL_INTERVAL / 1000.0,
                self._poll,
            )

    def _handle_recv(self):
        count = 0
        while True:
            try:
                msg = _SyncSocket.recv_multipart(self.socket, zmq.NOBLOCK)
                count += 1
            except zmq.ZMQError as e:
                if e.errno == zmq.EAGAIN:
                    break
                if _DEBUG:
                    _log(f'_handle_recv ZMQError: errno={e.errno} msg={e}')
                raise
            except Exception as ex:
                if _DEBUG:
                    _log(f'_handle_recv Exception: {type(ex).__name__}: {ex}')
                break

            if not self._recv_callbacks:
                self._recv_buffer.append(msg)
                if _DEBUG:
                    _log(f'_handle_recv buffered msg (no callbacks)')
                continue

            for cb in self._recv_callbacks:
                if _DEBUG:
                    _log(f'_handle_recv invoking callback {cb} count={count}')
                try:
                    _call_cb(cb, msg, getattr(self.io_loop, "asyncio_loop", None))
                except Exception:
                    _tb.print_exc()
        if count > 0 and _DEBUG:
            _log(f'_handle_recv read {count} msgs socket={self.socket} running={self._running} closed={self._closed} callbacks={len(self._recv_callbacks)}')

    def on_recv(self, callback, copy=None):
        if _DEBUG:
            _log(f'on_recv set callback={callback} on thread={threading.current_thread().name}')
        self._recv_callbacks = [callback]
        while self._recv_buffer:
            msg = self._recv_buffer.popleft()
            try:
                _call_cb(callback, msg, getattr(self.io_loop, "asyncio_loop", None))
            except Exception:
                _tb.print_exc()

    def on_recv_stream(self, callback, copy=None):
        def wrapper(msg):
            callback(self, msg)
        self._recv_callbacks = [wrapper]
        while self._recv_buffer:
            msg = self._recv_buffer.popleft()
            try:
                _call_cb(wrapper, msg)
            except Exception:
                _tb.print_exc()

    def stop_on_recv(self):
        """Stop calling recv callbacks. Received messages will be buffered."""
        self._recv_callbacks = []

    def on_recv_multipart(self, callback):
        self.on_recv(callback)

    def send(self, msg, flags=0, copy=True, track=False):
        _SyncSocket.send(self.socket, msg, flags)
        self._run_send_callbacks()

    def send_multipart(self, msg, flags=0, copy=True, track=False):
        _SyncSocket.send_multipart(self.socket, msg, flags)
        self._run_send_callbacks()

    def send_string(self, msg, flags=0):
        if isinstance(msg, str):
            msg = msg.encode()
        self.send(msg, flags)

    def _run_send_callbacks(self):
        cbs = self._send_callbacks
        self._send_callbacks = []
        for cb in cbs:
            try:
                cb(None)
            except Exception:
                _tb.print_exc()

    def closed(self):
        return self._closed

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._running = False
        if self.socket:
            self.socket.close()
            self.socket = None
        self._recv_callbacks = []
        self._send_callbacks = []
        self._recv_buffer.clear()

    def flush(self, flag=0):
        if self._flushed:
            return
        self._flushed = True
        try:
            while True:
                msg = _SyncSocket.recv_multipart(self.socket, zmq.NOBLOCK)
                if self._recv_callbacks:
                    for cb in self._recv_callbacks:
                        try:
                            _call_cb(cb, msg, getattr(self.io_loop, "asyncio_loop", None))
                        except Exception:
                            _tb.print_exc()
        except zmq.ZMQError:
            pass
        self._flushed = False

    def on_send(self, callback):
        self._send_callbacks.append(callback)

    def __del__(self):
        self.close()

    def __repr__(self):
        if self._closed:
            return '<ZMQStream closed>'
        return f'<ZMQStream at {hex(id(self))}>'

import threading  # noqa: E402 (needed for _log in __init__)
