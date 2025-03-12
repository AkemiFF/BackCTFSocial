# api/renderers.py
import json

from rest_framework.renderers import BrowsableAPIRenderer, JSONRenderer


class PrettyJSONRenderer(JSONRenderer):
    """
    Renderer which serializes to JSON with indentation.
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context and renderer_context.get('indent'):
            indent = renderer_context.get('indent')
        else:
            indent = 4
        
        return json.dumps(data, indent=indent, ensure_ascii=False).encode('utf-8')


class AdminBrowsableAPIRenderer(BrowsableAPIRenderer):
    """
    Browsable API renderer that is only available to admin users.
    """
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if renderer_context and renderer_context.get('request'):
            request = renderer_context.get('request')
            if not request.user.is_staff:
                return JSONRenderer().render(data, accepted_media_type, renderer_context)
        
        return super().render(data, accepted_media_type, renderer_context)