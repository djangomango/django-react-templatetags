from typing import Any

from django.core.serializers.json import DjangoJSONEncoder

from django_react_templatetags.mixins import RepresentationMixin


def json_encoder_cls_factory(context: Any) -> type[DjangoJSONEncoder]:
    """Create JSON encoder subclass configured with request or template context."""

    class ReqReactRepresentationJSONEncoder(ReactRepresentationJSONEncoder):
        """JSON encoder configured with request or template context."""

        context = None

    ReqReactRepresentationJSONEncoder.context = context
    return ReqReactRepresentationJSONEncoder


class ReactRepresentationJSONEncoder(DjangoJSONEncoder):
    """JSON encoder supporting objects implementing RepresentationMixin."""

    def default(self, o: Any) -> Any:
        """Serialize RepresentationMixin instance or fallback to default serializer."""
        if isinstance(o, RepresentationMixin):
            args = [getattr(self, "context", None)]
            args = [x for x in args if x is not None]

            return o.to_react_representation(*args)

        return super().default(o)
