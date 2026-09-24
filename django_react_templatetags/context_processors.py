from typing import Any


def react_context_processor(request: Any) -> dict[str, list[Any]]:
    """Expose global list of react components in template context."""
    return {
        "REACT_COMPONENTS": [],
    }
