import json
import logging
from typing import Any

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class SSRService:
    """Service handling standard HTTP server-side rendering for React components."""

    def load_or_empty(
        self,
        component: dict[str, Any],
        headers: dict[str, str] | None = None,
        ssr_context: Any = None,
    ) -> dict[str, Any]:
        """Request component SSR HTML or return empty structure on failure."""
        if headers is None:
            headers = {}

        request_json = json.dumps(
            {
                "componentName": component["name"],
                "props": component.get("json_obj") or json.loads(component["json"]),
                "context": ssr_context or {},
            }
        )

        try:
            inner_html = self.load(request_json, headers)
        except requests.exceptions.RequestException as e:
            inner_html = ""
            msg = f"SSR request to '{getattr(settings, 'REACT_RENDER_HOST', '')}' failed: {e.__class__.__name__}"
            logger.exception(msg)

        return {
            "html": inner_html,
            "params": {},
        }

    def load(self, request_json: str, headers: dict[str, str]) -> str:
        """Perform HTTP POST request to SSR render endpoint."""
        req = requests.post(
            settings.REACT_RENDER_HOST,
            timeout=get_request_timeout(),
            data=request_json,
            headers=headers,
        )

        req.raise_for_status()
        return req.text


def get_request_timeout() -> int | float:
    """Return configured SSR timeout in seconds."""
    if not hasattr(settings, "REACT_RENDER_TIMEOUT"):
        return 20

    return settings.REACT_RENDER_TIMEOUT
