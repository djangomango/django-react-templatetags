from typing import Any


class RepresentationMixin:
    """Mixin defining react representation serialization method."""

    def to_react_representation(self, context: Any = None) -> Any:
        """Convert model or object state to React props dictionary."""
        raise NotImplementedError("Missing property to_react_representation in class")
