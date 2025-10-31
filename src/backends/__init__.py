"""Backend implementations for DeepAgents file storage."""

# Unified backend system (from deepagents)
from .protocol import BackendProtocol, WriteResult, EditResult, FileInfo, GrepMatch
from .state import StateBackend
from .store import StoreBackend
from .filesystem import FilesystemBackend
from .composite import CompositeBackend

__all__ = [
    # Protocol and types
    "BackendProtocol",
    "WriteResult",
    "EditResult",
    "FileInfo",
    "GrepMatch",

    # Backends
    "StateBackend",
    "StoreBackend",
    "FilesystemBackend",
    "CompositeBackend",
]
