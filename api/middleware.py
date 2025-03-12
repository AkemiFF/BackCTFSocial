# api/middleware.py
import json
import time

from django.utils import timezone

from .models import ApiRequest


class ApiRequestMiddleware:
    """
    Middleware to track API requests.
    """
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip non-API requests
        if not request.path.startswith('/api/'):
            return self.get_response(request)
        
        # Record start time
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Calculate execution time
        execution_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Only log if this is an API request
        if request.path.startswith('/api/'):
            try:
                # Get request data
                request_data = None
                if request.method in ['POST', 'PUT', 'PATCH']:
                    if hasattr(request, 'data'):
                        request_data = request.data
                    else:
                        try:
                            request_data = json.loads(request.body.decode('utf-8'))
                        except:
                            pass
                
                # Get response data
                response_data = None
                if hasattr(response, 'data'):
                    response_data = response.data
                
                # Create API request record
                ApiRequest.objects.create(
                    user=request.user if request.user.is_authenticated else None,
                    path=request.path,
                    method=request.method,
                    status_code=response.status_code,
                    ip_address=self._get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    request_data=request_data,
                    response_data=response_data,
                    execution_time=execution_time
                )
            except Exception as e:
                # Log error but don't interrupt the request
                print(f"Error logging API request: {e}")
        
        return response
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip