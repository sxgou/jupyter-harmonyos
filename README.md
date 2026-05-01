# Jupyter Notebook for HarmonyOS

Run [Jupyter Notebook](https://jupyter.org/) on HarmonyOS (HongMeng Kernel)
using a ctypes-based ZMQ compatibility layer instead of the native pyzmq C extension.

## Problem

HarmonyOS SELinux policy blocks `dlopen()` from writable directories, making all C Python
extensions (`.so` files) unloadable. Jupyter depends on `pyzmq` (a C extension wrapping libzmq),
which cannot be installed or loaded on HarmonyOS.

Additionally, `referencing` (a Rust-native package used by `jupyter_events`) is also blocked.

## Solution

Two compatibility shims replace the native packages:

| Shim | Replaces | Approach |
|------|----------|----------|
| `zmq_shim` | `pyzmq` (C extension) | ctypes wrapper around system libzmq |
| `referencing_shim` | `referencing` (Rust) | Monkey-patches jsonschema |

## System Requirements

- HarmonyOS with HongMeng Kernel 1.12.0+
- Python 3.12 (system: `/data/service/hnp/python.org/python_3.12/bin/python3.12`)
- System libzmq 5.2.5 (`/data/service/hnp/python.org/python_3.12/lib/.../av.libs/libzmq-*.so.5.2.5`)
- pip 26+

## Installation

### 1. Install compatibility shims

```bash
PYTHON=/data/service/hnp/python.org/python_3.12/bin/python3.12
PIP="$PYTHON -m pip"

# Install ZMQ shim (ctypes-based)
$PIP install -e zmq_shim --no-build-isolation

# Install referencing shim
$PIP install -e referencing_shim --no-build-isolation
```

### 2. Install Jupyter components

```bash
# Jupyter packages (all --no-deps to prevent pulling pyzmq)
$PIP install ipykernel ipython jupyter_client jupyter_server notebook --no-deps

# tornado (pure-Python, needed by ipykernel)
$PIP install tornado
```

### 3. Apply ipykernel patches

The following patches to ipykernel's `kernelbase.py` and `kernelapp.py` are required
for the ZMQ shim compatibility (change `copy=False` to `copy=True`):

**File: `<site-packages>/ipykernel/kernelbase.py`**

```python
# In dispatch_shell(): change copy=False to copy=True
idents, msg = self.session.feed_identities(msg, copy=True)
msg = self.session.deserialize(msg, content=True, copy=True)

# In "stop aborting" check: change msg[0].buffer to msg[0]
if len(msg) == 1 and msg[0] == b"stop aborting":
```

**File: `<site-packages>/ipykernel/kernelapp.py`**

Remove diagnostic logging code from `init_kernel()` and `start()` methods.

### 4. Start Jupyter

```bash
# Via startup script (ensures correct sys.path order)
PYTHON=/data/service/hnp/python.org/python_3.12/bin/python3.12
$PYTHON -c "
import sys
_site = '/storage/Users/currentUser/.local/lib/python3.12/site-packages'
if '' in sys.path:
    sys.path.remove('')
sys.path.insert(0, _site)
from jupyter_server.serverapp import ServerApp
ServerApp.launch_instance(argv=['--port=8888', '--no-browser'])
"
```

## Architecture

```
Client (DEALER)
    │ TCP
    ▼
ROUTER socket (Kernel Process)
    │
    ▼ ZMQStream (ShellChannel, 50ms poll)
shell_channel_thread_main()
    │ parse header → get subshell_id
    │ forward via inproc PAIR
    ▼
_shell_channel_to_main (SocketPair)
    │
    ▼ ZMQStream (MainThread, 50ms poll)
shell_main() → dispatch_shell()
    │ → Kernel execution → reply
    ▼
main_to_shell_channel (SocketPair)
    │
    ▼ ZMQStream (ShellChannel)
_send_on_shell_channel() → shell_socket.send_multipart()
    │
    ▼ TCP → Client
```

### Thread structure

| Thread | Role | IOLoop |
|--------|------|--------|
| MainThread | Initialize, shell_main | AsyncIOMainLoop |
| ShellChannel | Receive shell ROUTER messages | AsyncIOLoop |
| Control | Handle control messages | AsyncIOLoop |
| IOPub | Publish status/output | AsyncIOLoop |
| Heartbeat | Heartbeat response | None (raw socket) |

## ZMQStream Implementation Notes

The ZMQStream is a polling-based implementation since HarmonyOS asyncio
doesn't support `add_reader()`:

- Poll interval: 50ms
- Non-blocking recv with `zmq.NOBLOCK`
- Coroutine-aware callback dispatch via `asyncio.run_coroutine_threadsafe()`

## Verification

```bash
# Test ZMQ shim
python -c "
import zmq
ctx = zmq.Context()
s = ctx.socket(zmq.PAIR)
s.bind('inproc://test')
s2 = ctx.socket(zmq.PAIR)
s2.connect('inproc://test')
s2.send(b'hello')
print(s.recv())  # Should output b'hello'
"

# Test kernel client
python test_kernel_client3.py
# Expected:
#   kernel_info_request → kernel_info_reply (status: ok)
#   execute_request → execute_reply (status: ok)
```

## Known Issues

| Issue | Cause | Workaround |
|-------|-------|------------|
| `copy=False` not supported | ZMQ shim returns `bytes` not `zmq.Message` | Use `copy=True` everywhere |
| `ModuleNotFoundError: comm` | Python resolves to ipykernel subpackage | Ensure site-packages before '' in sys.path |
| ZMQStream polling delay | 50ms poll instead of edge-triggered epoll | Acceptable for notebook use |
| No `zmq.Message` class | ctypes shim limitation | Use `bytes` directly |
| `ctx.term()` blocks on cleanup | Unclosed sockets | Use `ctx.destroy(linger=0)` |

## Related Projects

- [gfortran-harmonyos](https://github.com/sxgou/gfortran-harmonyos) — Fortran compiler for HarmonyOS
- [hermes-harmonyos](https://github.com/sxgou/hermes-harmonyos) — Hermes Agent for HarmonyOS
