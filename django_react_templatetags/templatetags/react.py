import json
import uuid
from typing import Any

from django import template
from django.conf import settings
from django.template import Node
from django.utils.module_loading import import_string
from django.utils.safestring import SafeString, mark_safe

from django_react_templatetags.encoders import json_encoder_cls_factory
from django_react_templatetags.ssr.default import SSRService

register = template.Library()

CONTEXT_KEY = "REACT_COMPONENTS"

DEFAULT_SSR_HEADERS = {
    "Content-type": "application/json",
    "Accept": "text/plain",
}


def get_uuid() -> str:
    """Generate unique hexadecimal string identifier."""
    return uuid.uuid4().hex


def has_ssr(request: Any) -> bool:
    """Determine whether server-side rendering is active for current request."""
    if request and request.META.get("HTTP_X_DISABLE_SSR"):
        return False

    return bool(hasattr(settings, "REACT_RENDER_HOST") and settings.REACT_RENDER_HOST)


def get_ssr_headers() -> dict[str, str]:
    """Retrieve HTTP headers configured for SSR requests."""
    if not hasattr(settings, "REACT_RENDER_HEADERS"):
        return DEFAULT_SSR_HEADERS
    return settings.REACT_RENDER_HEADERS


def load_from_ssr(component: dict[str, Any], ssr_context: Any = None) -> dict[str, Any]:
    """Invoke configured SSR service to render component HTML."""
    ssr_service = _get_ssr_service()()
    return ssr_service.load_or_empty(
        component,
        headers=get_ssr_headers(),
        ssr_context=ssr_context,
    )


def _get_ssr_service() -> type[Any]:
    """Load custom React SSR service class from settings or return default."""
    class_path = getattr(settings, "REACT_SSR_SERVICE", "")
    if not class_path:
        return SSRService

    return import_string(class_path)


class ReactTagManager(Node):
    """Template node managing placeholder markup generation and component registration."""

    def __init__(
        self,
        identifier: Any,
        component: Any,
        data: Any = None,
        css_class: Any = None,
        props: dict[str, Any] | None = None,
        ssr_context: Any = None,
        no_placeholder: Any = None,
    ) -> None:
        """Initialize ReactTagManager node parameters."""
        component_prefix = ""
        if hasattr(settings, "REACT_COMPONENT_PREFIX"):
            component_prefix = settings.REACT_COMPONENT_PREFIX

        self.identifier = identifier
        self.component = component
        self.component_prefix = component_prefix
        self.data = data
        self.css_class = css_class
        self.props = props or {}
        self.ssr_context = ssr_context
        self.no_placeholder = no_placeholder

    def render(self, context: Any) -> SafeString:
        """Render component placeholder or SSR content and update template context queue."""
        qualified_component_name = self.get_qualified_name(context)
        identifier = self.get_identifier(context, qualified_component_name)
        component_props = self.get_component_props(context)
        json_str = self.props_to_json(component_props, context)

        component = {
            "identifier": identifier,
            "data_identifier": f"{identifier}_data",
            "name": qualified_component_name,
            "json": json_str,
            "json_obj": json.loads(json_str),
        }

        placeholder_attr = [
            ("id", identifier),
            ("class", self.resolve_template_variable(self.css_class, context)),
        ]
        placeholder_attr = [x for x in placeholder_attr if x[1] is not None]

        component_html = ""
        if has_ssr(context.get("request", None)):
            ssr_resp = load_from_ssr(
                component,
                ssr_context=self.get_ssr_context(context),
            )
            component_html = ssr_resp["html"]
            component["ssr_params"] = ssr_resp["params"]

        components = context.get(CONTEXT_KEY, [])
        components.append(component)
        context[CONTEXT_KEY] = components

        if self.no_placeholder:
            return mark_safe(component_html)

        return mark_safe(self.render_placeholder(placeholder_attr, component_html))

    def get_qualified_name(self, context: Any) -> str:
        """Return prefixed component name resolved from context."""
        component_name = self.resolve_template_variable(self.component, context)
        return f"{self.component_prefix}{component_name}"

    def get_identifier(self, context: Any, qualified_component_name: str) -> str:
        """Return unique component identifier string."""
        identifier = self.resolve_template_variable(self.identifier, context)

        if identifier:
            return str(identifier)

        return f"{qualified_component_name}_{get_uuid()}"

    def get_component_props(self, context: Any) -> dict[str, Any]:
        """Resolve and combine dictionary data and individual component props."""
        resolved_data = self.resolve_template_variable_else_none(self.data, context)
        resolved_data = resolved_data if resolved_data else {}

        for prop in self.props:
            data = self.resolve_template_variable_else_none(
                self.props[prop],
                context,
            )
            resolved_data[prop] = data

        return resolved_data

    def get_ssr_context(self, context: Any) -> Any:
        """Resolve SSR context variable or return empty dictionary."""
        if not self.ssr_context:
            return {}

        return self.resolve_template_variable(self.ssr_context, context)

    @staticmethod
    def resolve_template_variable(value: Any, context: Any) -> Any:
        """Resolve value from template context if it is a template Variable."""
        if isinstance(value, template.Variable):
            return value.resolve(context)

        return value

    @staticmethod
    def resolve_template_variable_else_none(value: Any, context: Any) -> Any:
        """Safely resolve variable from context or return None on resolution error."""
        try:
            data = value.resolve(context)
        except (template.VariableDoesNotExist, AttributeError):
            data = None

        return data

    @staticmethod
    def props_to_json(resolved_data: Any, context: Any) -> str:
        """Serialize props dictionary to JSON string using custom encoder."""
        cls = json_encoder_cls_factory(context)
        return json.dumps(resolved_data, cls=cls)

    @staticmethod
    def render_placeholder(attributes: list[tuple[str, Any]], component_html: str = "") -> str:
        """Render HTML div placeholder container with given attributes."""
        attr_pairs = [f'{k}="{v}"' for k, v in attributes]
        joined = " ".join(attr_pairs)
        space = f" {joined}" if joined else ""
        return f"<div{space}>{component_html}</div>"


@register.tag
def react_render(parser: Any, token: Any) -> Node:
    """Render a react placeholder and append component to global render queue."""
    values = _prepare_args(parser, token)
    tag_manager = _get_tag_manager()
    return tag_manager(**values)


def _prepare_args(parser: Any, token: Any) -> dict[str, Any]:
    """Parse tag arguments and map them to tag manager constructor parameters."""
    values: dict[str, Any] = {
        "identifier": None,
        "css_class": None,
        "data": None,
        "props": {},
    }

    key_mapping = {
        "id": "identifier",
        "class": "css_class",
        "props": "data",
    }

    args = token.split_contents()
    method = args[0]

    for arg in args[1:]:
        key, value = arg.split("=")

        key = key_mapping.get(key, key)
        is_standalone_prop = key.startswith("prop_")
        if is_standalone_prop:
            key = key[5:]

        var_value = template.Variable(value)
        if is_standalone_prop:
            values["props"][key] = var_value
        else:
            values[key] = var_value

    assert "component" in values, f"{method} is missing component value"

    return values


def _get_tag_manager() -> type[Any]:
    """Load custom React Tag Manager class from settings or return default."""
    class_path = getattr(settings, "REACT_RENDER_TAG_MANAGER", "")
    if not class_path:
        return ReactTagManager

    return import_string(class_path)


@register.inclusion_tag("react_print.html", takes_context=True)
def react_print(context: Any) -> Any:
    """Render ReactDOM hydration script markup for all queued React components."""
    components = context.get(CONTEXT_KEY, [])
    context[CONTEXT_KEY] = []

    new_context = context.__copy__()
    new_context["ssr_available"] = has_ssr(context.get("request", None))
    new_context["components"] = components

    return new_context
