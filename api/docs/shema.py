# api/docs/schema.py
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_bearer_security_scheme_object


class JWTScheme(OpenApiAuthenticationExtension):
    target_class = 'api.authentication.CustomJWTAuthentication'
    name = 'JWT Authentication'
    
    def get_security_definition(self, auto_schema):
        return build_bearer_security_scheme_object(
            header_name='Authorization',
            token_prefix='Bearer',
            bearer_format='JWT',
        )


class ApiKeyScheme(OpenApiAuthenticationExtension):
    target_class = 'api.authentication.ApiKeyAuthentication'
    name = 'API Key'
    
    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'header',
            'name': 'X-API-Key',
            'description': 'API key authentication',
        }