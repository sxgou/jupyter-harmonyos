"""ZMQ log handlers (minimal stub for ipykernel compatibility)."""
import logging


class PUBHandler(logging.Handler):
    """A logging handler that publishes messages via ZMQ PUB socket.

    Stub implementation for compatibility.
    """
    def __init__(self, socket, root_topic=''):
        self.socket = socket
        self.root_topic = root_topic
        super().__init__()

    def emit(self, record):
        """Emit a log record over the PUB socket."""
        try:
            msg = self.format(record).encode('utf-8')
            topic = self.root_topic
            if topic:
                msg = topic.encode() + b' ' + msg
            self.socket.send(msg)
        except Exception:
            self.handleError(record)
