"""Application-specific errors with user-facing diagnostics."""


class FlyInError(Exception):
    """Base class for anticipated Fly-in failures."""


class GraphError(FlyInError):
    """Raised when a graph invariant would be violated."""


class ParseError(FlyInError):
    """Raised when a map cannot be parsed."""


class UnsolvableMapError(FlyInError):
    """Raised when a valid map has no route to its destination."""


class SimulationError(FlyInError):
    """Raised when a simulation cannot make valid progress."""
