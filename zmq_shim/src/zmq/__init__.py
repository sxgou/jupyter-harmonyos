"""Pure-Python ZMQ shim using ctypes to wrap system libzmq.

Provides a drop-in replacement for pyzmq on HarmonyOS where native
C extensions cannot be loaded due to SELinux restrictions.
"""
import ctypes
import threading
from typing import Any, Callable

__version__ = '4.3.5'

# ── Load libzmq via ctypes ────────────────────────────────────────────────

_av_libs = '/data/service/hnp/python.org/python_3.12/lib/python3.12/site-packages/av.libs'
_lib = ctypes.CDLL(f'{_av_libs}/libzmq-9780a160.so.5.2.5', mode=2)


def _c(name, restype, argtypes):
    fn = getattr(_lib, name)
    fn.restype = restype
    fn.argtypes = argtypes
    return fn


# ── Core C function wrappers ──────────────────────────────────────────────

_zmq_ctx_new = _c('zmq_ctx_new', ctypes.c_void_p, [])
_zmq_ctx_destroy = _c('zmq_ctx_destroy', ctypes.c_int, [ctypes.c_void_p])
_zmq_ctx_term = _c('zmq_ctx_term', ctypes.c_int, [ctypes.c_void_p])
_zmq_ctx_shutdown = _c('zmq_ctx_shutdown', ctypes.c_int, [ctypes.c_void_p])
_zmq_ctx_set = _c('zmq_ctx_set', ctypes.c_int, [ctypes.c_void_p, ctypes.c_int, ctypes.c_int])
_zmq_ctx_get = _c('zmq_ctx_get', ctypes.c_int, [ctypes.c_void_p, ctypes.c_int])
_zmq_socket = _c('zmq_socket', ctypes.c_void_p, [ctypes.c_void_p, ctypes.c_int])
_zmq_close = _c('zmq_close', ctypes.c_int, [ctypes.c_void_p])
_zmq_bind = _c('zmq_bind', ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p])
_zmq_connect = _c('zmq_connect', ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p])
_zmq_unbind = _c('zmq_unbind', ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p])
_zmq_disconnect = _c('zmq_disconnect', ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p])
_zmq_send = _c('zmq_send', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int])
_zmq_recv = _c('zmq_recv', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int])
_zmq_setsockopt = _c('zmq_setsockopt', ctypes.c_int, [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_size_t])
_zmq_getsockopt = _c('zmq_getsockopt', ctypes.c_int, [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(ctypes.c_size_t)])
_zmq_errno = _c('zmq_errno', ctypes.c_int, [])
_zmq_strerror = _c('zmq_strerror', ctypes.c_char_p, [ctypes.c_int])
_zmq_poll = _c('zmq_poll', ctypes.c_int, [ctypes.c_void_p, ctypes.c_int, ctypes.c_long])
_zmq_proxy = _c('zmq_proxy', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p])
_zmq_proxy_steerable = _c('zmq_proxy_steerable', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p])
_zmq_msg_init = _c('zmq_msg_init', ctypes.c_int, [ctypes.c_void_p])
_zmq_msg_init_size = _c('zmq_msg_init_size', ctypes.c_int, [ctypes.c_void_p, ctypes.c_size_t])
_zmq_msg_send = _c('zmq_msg_send', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int])
_zmq_msg_recv = _c('zmq_msg_recv', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int])
_zmq_msg_close = _c('zmq_msg_close', ctypes.c_int, [ctypes.c_void_p])
_zmq_msg_data = _c('zmq_msg_data', ctypes.c_void_p, [ctypes.c_void_p])
_zmq_msg_size = _c('zmq_msg_size', ctypes.c_size_t, [ctypes.c_void_p])
_zmq_msg_more = _c('zmq_msg_more', ctypes.c_int, [ctypes.c_void_p])
_zmq_msg_move = _c('zmq_msg_move', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p])
_zmq_msg_copy = _c('zmq_msg_copy', ctypes.c_int, [ctypes.c_void_p, ctypes.c_void_p])
_zmq_socket_monitor = _c('zmq_socket_monitor', ctypes.c_int, [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int])
_zmq_has = _c('zmq_has', ctypes.c_int, [ctypes.c_char_p])
_zmq_device = _c('zmq_device', ctypes.c_int, [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p])
_zmq_sleep = _c('zmq_sleep', ctypes.c_int, [ctypes.c_int])

# zmq_version(int *major, int *minor, int *patch)
_zmq_version_raw = _c('zmq_version', None, [ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int)])

# ── zmq_msg_t structure (64 bytes on aarch64) ─────────────────────────────

class zmq_msg_t(ctypes.Structure):
    _fields_ = [("data", ctypes.c_ubyte * 64)]


# ── Constants ─────────────────────────────────────────────────────────────

# Socket types
PAIR = 0
PUB = 1
SUB = 2
REQ = 3
REP = 4
DEALER = 5
ROUTER = 6
PULL = 7
PUSH = 8
XPUB = 9
XSUB = 10
STREAM = 11
SERVER = 12
CLIENT = 13
RADIO = 14
DISH = 15
GATHER = 16
SCATTER = 17
DGRAM = 18
PEER = 19
CHANNEL = 20

# Socket options
AFFINITY = 4
IDENTITY = 5
SUBSCRIBE = 6
UNSUBSCRIBE = 7
RATE = 8
RECOVERY_IVL = 9
SNDBUF = 11
RCVBUF = 12
RCVMORE = 13
FD = 14
EVENTS = 15
TYPE = 16
LINGER = 17
RECONNECT_IVL = 18
RECONNECT_IVL_MAX = 19
BACKLOG = 23
RECOVERY_IVL_MSEC = 30
RECONNECT_IVL_MAX = 31
MAXMSGSIZE = 32
SNDHWM = 23
RCVHWM = 22
MULTICAST_HOPS = 25
RCVTIMEO = 27
SNDTIMEO = 28
SNDMORE = 2  # flag for send/recv
IMMEDIATE = 39
DONTWAIT = 1  # flag for send/recv
PROBE_ROUTER = 51
ROUTER_HANDOVER = 52
ROUTER_MANDATORY = 53
LAST_ENDPOINT = 32
TCP_KEEPALIVE = 34
TCP_KEEPALIVE_CNT = 35
TCP_KEEPALIVE_IDLE = 36
TCP_KEEPALIVE_INTVL = 37
CONNECT_TIMEOUT = 79
HEARTBEAT_IVL = 75
HEARTBEAT_TTL = 76
HEARTBEAT_TIMEOUT = 77
CONFLATE = 70
CURVE_SERVER = 72
CURVE_PUBLICKEY = 73
CURVE_SECRETKEY = 74
CURVE_SERVERKEY = 75
ZAP_DOMAIN = 68
PLAIN_SERVER = 61
PLAIN_USERNAME = 62
PLAIN_PASSWORD = 63
SOCKS_PROXY = 68
XPUB_VERBOSE = 40
XPUB_VERBOSER = 78
REQ_CORRELATE = 52
REQ_RELAXED = 53
ROUTER_RAW = 80
PRIORITY = 81
BINDTODEVICE = 83
USE_FD = 84
HANDSHAKE_IVL = 81
CONNECT_RID = 81
MECHANISM = 82
GSSAPI_SERVER = 82
GSSAPI_PRINCIPAL = 84
GSSAPI_SERVICE_PRINCIPAL = 86
GSSAPI_PLAINTEXT = 87
SOCKS_USERNAME = 89
SOCKS_PASSWORD = 90
INVERT_MATCHING = 91
XPUB_MANUAL = 92
XPUB_WELCOME_MSG = 93
STREAM_NOTIFY = 94
NOTIFY = 95
XPUB_MANUAL_LAST_VALUE = 96
ROUTER_NOTIFY = 97
MULTICAST_LOOP = 99
CONNECT_INTERVAL = 100
VMCI_BUFFER_SIZE = 101
VMCI_BUFFER_MIN_SIZE = 102
VMCI_BUFFER_MAX_SIZE = 103
VMCI_CONNECT_TIMEOUT = 104
APP_METADATA = 105
CONNECT_TIMEOUT = 106
GROUP_MAX_LENGTH = 107
THREAD_PRIORITY = 108
THREAD_SCHED_POLICY = 109
AFFINITY = 110
ROUTING_ID = 111
CONNECT_ROUTING_ID = 112
PRIORITY = 113
CONNECT_INTERVAL = 114

# Context options
IO_THREADS = 1
MAX_SOCKETS = 2
SOCKET_LIMIT = 3
THREAD_PRIORITY = 3
THREAD_SCHED_POLICY = 4
BLOCKY = 4
MSG_T_SIZE = 5
THREAD_AFFINITY_CPU_ADD = 7
THREAD_AFFINITY_CPU_REMOVE = 8
THREAD_NAME_PREFIX = 9
ZERO_COPY_RECV = 10

# Poll events
POLLIN = 1
POLLOUT = 2
POLLERR = 4

# Send/Recv flags
NOBLOCK = 1
SNDMORE = 2

# Error codes
EAGAIN = 11
EINVAL = 22
EFAULT = 14
EINTR = 4
EADDRINUSE = 98
ENOTSOCK = 88
ETERM = 156384765
EFSM = 156384768
ENOTSUP = 156384771
EALREADY = 156384768
EHOSTUNREACH = 113
EMTHREAD = 156384772

# Device types
STREAMER = 1
FORWARDER = 2
QUEUE = 3

# Security mechanism
NULL = 0
PLAIN = 1
CURVE = 2
GSSAPI = 3

# Event flags for monitor
EVENT_CONNECTED = 1
EVENT_CONNECT_DELAYED = 2
EVENT_CONNECT_RETRIED = 4
EVENT_LISTENING = 8
EVENT_BIND_FAILED = 16
EVENT_ACCEPTED = 32
EVENT_ACCEPT_FAILED = 64
EVENT_CLOSED = 128
EVENT_CLOSE_FAILED = 256
EVENT_DISCONNECTED = 512
EVENT_MONITOR_STOPPED = 1024
EVENT_ALL = 65535

# ── ZMQVersion Support ────────────────────────────────────────────────────

def zmq_version():
    """Return (major, minor, patch) tuple."""
    m, n, p = ctypes.c_int(), ctypes.c_int(), ctypes.c_int()
    _zmq_version_raw(ctypes.byref(m), ctypes.byref(n), ctypes.byref(p))
    return (m.value, n.value, p.value)


def pyzmq_version():
    """Return pyzmq version (our shim version)."""
    return __version__


def pyzmq_version_info():
    """Return pyzmq version as tuple."""
    return tuple(int(x) for x in __version__.split('.'))


# ── Error Handling ────────────────────────────────────────────────────────

def _check_rc(rc):
    """Check return code and raise ZMQError if < 0."""
    if rc < 0:
        err = _zmq_errno()
        raise ZMQError(err, _zmq_strerror(err).decode())
    return rc


class ZMQError(Exception):
    """ZMQ error with errno."""
    def __init__(self, errno=None, msg=''):
        self.errno = errno
        super().__init__(msg or _zmq_strerror(errno).decode() if errno else '')

    def __str__(self):
        return f'ZMQError(errno={self.errno}): {self.args[0]}' if self.errno else self.args[0]


class ZMQVersionError(NotImplementedError):
    """Raised when a feature is not available in the current ZMQ version."""
    pass


class Context:
    """ZMQ Context wrapper."""

    _instance_lock = threading.Lock()
    _instance = None
    _socket_class = None  # set by ioloop manager at runtime

    def __class_getitem__(cls, item):
        return cls

    def __init__(self, io_threads=1, **kwargs):
        self._handle = _zmq_ctx_new()
        if not self._handle:
            raise ZMQError(_zmq_errno(), "Failed to create context")
        self._shadowed = False
        self._sockets = set()
        self._sockets_lock = threading.Lock()
        if io_threads != 1:
            self.set(IO_THREADS, io_threads)

    @property
    def closed(self):
        """True if context has been terminated."""
        return self._handle is None

    @classmethod
    def instance(cls, io_threads=1):
        """Return or create the global Context singleton."""
        if cls._instance is not None:
            return cls._instance
        with cls._instance_lock:
            if cls._instance is None:
                cls._instance = cls(io_threads=io_threads)
        return cls._instance

    def set(self, option, value):
        return _check_rc(_zmq_ctx_set(self._handle, option, value))

    def get(self, option):
        return _zmq_ctx_get(self._handle, option)

    def socket(self, socket_type, **kwargs):
        sock = _zmq_socket(self._handle, socket_type)
        if not sock:
            raise ZMQError(_zmq_errno(), "Failed to create socket")
        s = Socket(sock, socket_type, context=self, **kwargs)
        with self._sockets_lock:
            self._sockets.add(s)
        return s

    def term(self):
        if self._handle:
            _zmq_ctx_term(self._handle)
            self._handle = None
            with self._sockets_lock:
                for s in list(self._sockets):
                    s._handle = None
                self._sockets.clear()
            if Context._instance is self:
                Context._instance = None

    def destroy(self, linger=None):
        if linger is not None:
            with self._sockets_lock:
                for s in list(self._sockets):
                    try:
                        s.set(LINGER, linger)
                    except ZMQError:
                        pass
        self.term()

    def __del__(self):
        if self._handle and not self._shadowed:
            _zmq_ctx_destroy(self._handle)
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.term()

    @property
    def underlying(self):
        return self._handle

    def __int__(self):
        return self._handle.__hash__() if self._handle else 0


class Socket:
    """ZMQ Socket wrapper."""

    def __class_getitem__(cls, item):
        return cls

    def __init__(self, handle=None, socket_type=PAIR, context=None, **kwargs):
        if handle is None:
            self._new_socket(context, socket_type)
        else:
            self._handle = handle
            self._type = socket_type
            self._context = context
            self._closed = False

    def _new_socket(self, context, socket_type):
        if context is None:
            context = Context.instance()
        self._context = context
        self._type = socket_type
        self._handle = _zmq_socket(context._handle, socket_type)
        if not self._handle:
            raise ZMQError(_zmq_errno(), "Failed to create socket")
        self._closed = False
        with context._sockets_lock:
            context._sockets.add(self)

    @classmethod
    def shadow(cls, handle):
        """Create a Socket from an existing zmq handle."""
        s = cls.__new__(cls)
        s._handle = ctypes.c_void_p(int(handle)).value if hasattr(handle, 'value') else handle
        s._context = None
        s._type = 0
        s._closed = False
        return s

    def bind(self, addr):
        return _check_rc(_zmq_bind(self._handle, addr.encode() if isinstance(addr, str) else addr))

    def connect(self, addr):
        return _check_rc(_zmq_connect(self._handle, addr.encode() if isinstance(addr, str) else addr))

    def unbind(self, addr):
        return _check_rc(_zmq_unbind(self._handle, addr.encode() if isinstance(addr, str) else addr))

    def disconnect(self, addr):
        return _check_rc(_zmq_disconnect(self._handle, addr.encode() if isinstance(addr, str) else addr))

    def close(self, linger=None):
        if self._closed or not self._handle:
            return
        if linger is not None:
            try:
                self.set(LINGER, linger)
            except ZMQError:
                pass
        _zmq_close(self._handle)
        self._closed = True
        self._handle = None
        if self._context:
            with self._context._sockets_lock:
                self._context._sockets.discard(self)

    def set(self, option, value):
        if isinstance(value, str):
            value = value.encode()
        if isinstance(value, int):
            val = ctypes.c_int(value)
            buf = ctypes.byref(val)
            size = ctypes.sizeof(val)
        elif isinstance(value, bytes):
            buf = value
            size = len(value)
        else:
            buf = value
            size = len(value)
        return _check_rc(_zmq_setsockopt(self._handle, option, buf, size))

    def get(self, option):
        if option == TYPE:
            return self._type
        # Try integer-sized buffer first
        val = ctypes.c_int()
        size = ctypes.c_size_t(ctypes.sizeof(val))
        rc = _zmq_getsockopt(self._handle, option, ctypes.byref(val), ctypes.byref(size))
        if rc == 0:
            return val.value
        # If EINVAL, option likely returns a string (e.g. LAST_ENDPOINT)
        # Retry with a larger buffer: query size, then read
        buf = ctypes.create_string_buffer(1024)
        buf_size = ctypes.c_size_t(1024)
        rc = _zmq_getsockopt(self._handle, option, buf, ctypes.byref(buf_size))
        if rc == 0:
            return buf.value.decode()
        raise ZMQError(_zmq_errno())

    def getsockopt(self, option):
        return self.get(option)

    def setsockopt(self, option, value):
        return self.set(option, value)

    def fileno(self):
        """Return the socket's file descriptor (for IOLoop registration)."""
        return self.getsockopt(14)  # ZMQ_FD = 14

    def send(self, data, flags=0):
        if isinstance(data, str):
            data = data.encode()
        buf = ctypes.create_string_buffer(data) if isinstance(data, bytes) else data
        length = len(data) if isinstance(data, bytes) else len(bytes(data))
        return _check_rc(_zmq_send(self._handle, buf, length, flags))

    def recv(self, flags=0, copy=True, track=False):
        # First, get size hint via ZMQ_RCVMORE or use a large buffer approach
        # Actually, recv with a buffer of unknown size is tricky.
        # For ZMQ, we need to use zmq_msg_recv for variable-length messages.
        msg = zmq_msg_t()
        _zmq_msg_init(ctypes.byref(msg))
        try:
            rc = _zmq_msg_recv(ctypes.byref(msg), self._handle, flags)
            if rc < 0:
                err = _zmq_errno()
                if err == EAGAIN:
                    raise ZMQError(err, "Resource temporarily unavailable")
                raise ZMQError(err)
            data_ptr = _zmq_msg_data(ctypes.byref(msg))
            size = _zmq_msg_size(ctypes.byref(msg))
            return ctypes.string_at(data_ptr, size)
        finally:
            _zmq_msg_close(ctypes.byref(msg))

    def recv_multipart(self, flags=0, copy=True, track=False):
        """Receive a multipart message."""
        parts = []
        msg = zmq_msg_t()
        while True:
            _zmq_msg_init(ctypes.byref(msg))
            rc = _zmq_msg_recv(ctypes.byref(msg), self._handle, flags)
            if rc < 0:
                _zmq_msg_close(ctypes.byref(msg))
                err = _zmq_errno()
                if err == EAGAIN and not parts:
                    raise ZMQError(err, "Resource temporarily unavailable")
                break
            data_ptr = _zmq_msg_data(ctypes.byref(msg))
            size = _zmq_msg_size(ctypes.byref(msg))
            parts.append(ctypes.string_at(data_ptr, size))
            more = _zmq_msg_more(ctypes.byref(msg))
            _zmq_msg_close(ctypes.byref(msg))
            if not more:
                break
        return parts

    def send_multipart(self, msg_parts, flags=0, copy=True, track=False):
        """Send a multipart message."""
        for i, part in enumerate(msg_parts):
            if isinstance(part, str):
                part = part.encode()
            f = flags | (SNDMORE if i < len(msg_parts) - 1 else 0)
            buf = ctypes.create_string_buffer(part) if isinstance(part, bytes) else part
            length = len(part) if isinstance(part, bytes) else len(bytes(part))
            rc = _zmq_send(self._handle, buf, length, f)
            if rc < 0:
                raise ZMQError(_zmq_errno())
        return len(msg_parts)

    def bind_to_random_port(self, addr, min_port=49152, max_port=65536, max_tries=100):
        """Bind to a random port."""
        import random
        addr = addr.encode() if isinstance(addr, str) else addr
        for _ in range(max_tries):
            port = random.randint(min_port, max_port - 1)
            full = addr + b':%d' % port
            rc = _zmq_bind(self._handle, full)
            if rc == 0:
                return port
        raise ZMQError(_zmq_errno(), "Could not bind to a random port")

    def monitor(self, addr, events=EVENT_ALL):
        """Monitor socket events."""
        addr = addr.encode() if isinstance(addr, str) else addr
        return _check_rc(_zmq_socket_monitor(self._handle, addr, events))

    @property
    def closed(self):
        return self._closed

    @property
    def context(self):
        return self._context

    @context.setter
    def context(self, ctx):
        self._context = ctx

    @property
    def underlying(self):
        return self._handle

    @property
    def linger(self):
        return self.get(LINGER)

    @linger.setter
    def linger(self, value):
        self.set(LINGER, value)

    @property
    def fd(self):
        return self.get(FD)

    @property
    def last_endpoint(self):
        return self.get(LAST_ENDPOINT)

    def __del__(self):
        if not getattr(self, '_closed', True) and getattr(self, '_handle', None):
            try:
                _zmq_close(self._handle)
            except Exception:
                pass
            self._handle = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __int__(self):
        return self._handle.__hash__() if self._handle else 0

    def get_hwm(self):
        """Get high water mark."""
        return self.get(SNDHWM)

    def set_hwm(self, value):
        """Set high water mark."""
        self.set(SNDHWM, value)
        self.set(RCVHWM, value)

    hwm = property(get_hwm, set_hwm)


# ── Poller ────────────────────────────────────────────────────────────────

class Poller:
    """ZMQ Poller."""

    class _POLLITEM(ctypes.Structure):
        _fields_ = [
            ("socket", ctypes.c_void_p),
            ("fd", ctypes.c_int),
            ("events", ctypes.c_short),
            ("revents", ctypes.c_short),
        ]

    def __init__(self):
        self._items = {}  # socket -> (socket_obj, events)
        self._fd_items = {}  # fd -> (socket_obj, events)

    def register(self, socket, flags=POLLIN):
        if isinstance(socket, int):
            self._fd_items[socket] = (None, flags)
        else:
            self._items[socket] = (socket, flags)

    def unregister(self, socket):
        if isinstance(socket, int):
            self._fd_items.pop(socket, None)
        else:
            self._items.pop(socket, None)

    def poll(self, timeout=None):
        """Poll for events. timeout in milliseconds (None = infinite, 0 = return immediately)."""
        if not self._items and not self._fd_items:
            return []

        items_list = []
        fd_timeout = None

        for sock, (sock_obj, flags) in self._items.items():
            handle = sock._handle if hasattr(sock, '_handle') else sock
            item = self._POLLITEM()
            item.socket = handle if hasattr(sock, '_handle') else None
            item.fd = 0
            item.events = flags
            item.revents = 0
            items_list.append((item, sock))

        for fd, (_, flags) in self._fd_items.items():
            item = self._POLLITEM()
            item.socket = None
            item.fd = fd
            item.events = flags
            item.revents = 0
            items_list.append((item, fd))

        if not items_list:
            return []

        poll_array = (self._POLLITEM * len(items_list))()
        for i, (item, _) in enumerate(items_list):
            poll_array[i] = item

        to = -1 if timeout is None else timeout
        rc = _zmq_poll(poll_array, len(items_list), to)
        if rc < 0:
            err = _zmq_errno()
            if err == EINTR:
                return []
            raise ZMQError(err)

        result = []
        for i, (_, obj) in enumerate(items_list):
            revents = poll_array[i].revents
            if revents:
                result.append((obj, revents))
        return result


# ── Device / Proxy ────────────────────────────────────────────────────────

def device(device_type, frontend, backend):
    """Run a ZMQ device (proxy)."""
    fh = frontend._handle if hasattr(frontend, '_handle') else frontend
    bh = backend._handle if hasattr(backend, '_handle') else backend
    rc = _zmq_device(device_type, fh, bh)
    if rc < 0:
        err = _zmq_errno()
        if err == ETERM:
            raise ZMQError(err, "Context was terminated")
        raise ZMQError(err)
    return rc


def proxy(frontend, backend, capture=None):
    """Run a ZMQ proxy."""
    fh = frontend._handle if hasattr(frontend, '_handle') else frontend
    bh = backend._handle if hasattr(backend, '_handle') else backend
    ch = capture._handle if hasattr(capture, '_handle') else (capture or 0)
    if ch is None:
        ch = 0
    rc = _zmq_proxy(fh, bh, ch)
    if rc < 0:
        err = _zmq_errno()
        if err == ETERM:
            raise ZMQError(err, "Context was terminated")
        raise ZMQError(err)
    return rc


# ── MessageTracker (sentinel for async send tracking) ─────────────────────

class MessageTracker:
    """Tracks a list of unfinished messages (stub).

    In pyzmq, this tracks the zmq.Message objects that have been
    sent with copy=False. Our shim always copies, so this is a no-op.
    """
    def __init__(self, *args, **kwargs):
        self.done = True

    def done(self):
        return True

    def wait(self, timeout=None):
        return True

    def __repr__(self):
        return '<MessageTracker: done>'

    def __bool__(self):
        return True


# ── Utility functions ─────────────────────────────────────────────────────

def strerror(errno):
    """Return string description of ZMQ error."""
    return _zmq_strerror(errno).decode()


def zmq_errno():
    """Return current ZMQ errno."""
    return _zmq_errno()


def has(capability):
    """Check if ZMQ has a capability."""
    return bool(_zmq_has(capability.encode() if isinstance(capability, str) else capability))


# ── Socket types mapping ──────────────────────────────────────────────────

_socket_types = {
    PAIR: 'PAIR', PUB: 'PUB', SUB: 'SUB', REQ: 'REQ', REP: 'REP',
    DEALER: 'DEALER', ROUTER: 'ROUTER', PULL: 'PULL', PUSH: 'PUSH',
    XPUB: 'XPUB', XSUB: 'XSUB', STREAM: 'STREAM',
}

# ── Import submodules for namespace compatibility ────────────────────────

# Ensure zmq.sugar is available as a submodule (used by jupyter_client)
import zmq.sugar  # isort:skip
import zmq.sugar.socket  # isort:skip

# ── Re-exported from submodules ───────────────────────────────────────────

SUBSYSTEM = None
STOP = None


__all__ = [
    'Context', 'Socket', 'Poller', 'MessageTracker',
    'ZMQError', 'ZMQVersionError',
    'zmq_version', 'pyzmq_version', 'pyzmq_version_info',
    'strerror', 'zmq_errno', 'has',
    'device', 'proxy',
    # Constants
    'PAIR', 'PUB', 'SUB', 'REQ', 'REP', 'DEALER', 'ROUTER',
    'PULL', 'PUSH', 'XPUB', 'XSUB', 'STREAM',
    'POLLIN', 'POLLOUT', 'POLLERR',
    'NOBLOCK', 'SNDMORE', 'DONTWAIT',
    'LINGER', 'FD', 'EVENTS', 'TYPE', 'IDENTITY',
    'SUBSCRIBE', 'UNSUBSCRIBE',
    'SNDHWM', 'RCVHWM', 'RCVTIMEO', 'SNDTIMEO',
    'EAGAIN', 'EINTR', 'ETERM', 'ENOTSOCK', 'EADDRINUSE',
    'STREAMER', 'FORWARDER', 'QUEUE',
    'EVENT_ALL',
    'IO_THREADS', 'MAX_SOCKETS',
]
