"""
Centralized ID generation utilities for VOXY Agents.
"""

import hashlib
import threading
import time
import uuid
from typing import Optional

# Thread-safe counter for ensuring uniqueness
_counter_lock = threading.Lock()
_counter = 0


def generate_unique_request_id(session_id: Optional[str] = None) -> str:
    """
    Generate a globally unique request ID using multiple entropy sources.

    Args:
        session_id: Optional session ID to include in hash

    Returns:
        str: Unique request ID in UUID format
    """
    global _counter

    with _counter_lock:
        _counter += 1
        counter_value = _counter

    # Multiple entropy sources for maximum uniqueness
    timestamp_ns = int(time.time() * 1_000_000_000)  # nanoseconds
    thread_id = threading.get_ident()  # current thread ID
    process_id = hash(id(object()))  # process-specific hash
    session_hash = hashlib.md5((session_id or "").encode()).hexdigest()[:8]
    random_uuid = str(uuid.uuid4())

    # Combine all entropy sources
    hash_input = f"request_{timestamp_ns}_{thread_id}_{process_id}_{counter_value}_{session_hash}_{random_uuid}".encode()
    hash_digest = hashlib.sha256(hash_input).hexdigest()

    # Format as UUID
    return f"{hash_digest[:8]}-{hash_digest[8:12]}-{hash_digest[12:16]}-{hash_digest[16:20]}-{hash_digest[20:32]}"
