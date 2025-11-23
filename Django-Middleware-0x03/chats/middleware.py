import os
import logging
from datetime import datetime, time
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseForbidden

class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware that logs each user's requests to a file, including timestamp, user and request path.
    """
    
    def __init__(self, get_response=None):
        """
        Initialize the middleware.
        """
        self.get_response = get_response
        # Set up logging
        self.setup_logging()
    
    def setup_logging(self):
        """
        Configure logging to write to requests.log file.
        """
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(settings.BASE_DIR, 'logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # Configure logger
        self.logger = logging.getLogger('request_logger')
        self.logger.setLevel(logging.INFO)
        
        # Avoid adding multiple handlers if the logger already has them
        if not self.logger.handlers:
            # Create file handler
            log_file = os.path.join(log_dir, 'requests.log')
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            file_handler.setFormatter(formatter)
            
            # Add handler to logger
            self.logger.addHandler(file_handler)
            
            # Prevent the logger from propagating to the root logger
            self.logger.propagate = False
    
    def __call__(self, request):
        """
        Process the request and log the required information.
        """
        # Get the response by calling the next middleware/view
        response = self.get_response(request)
        
        # Log the request information
        self.log_request(request)
        
        return response
    
    def log_request(self, request):
        """
        Log the request details including timestamp, user, and path.
        """
        try:
            # Get user information
            if hasattr(request, 'user') and request.user.is_authenticated:
                user = request.user.email or request.user.username
            else:
                user = 'Anonymous'
            
            # Get current timestamp
            timestamp = datetime.now()
            
            # Get request path
            path = request.path
            
            # Log the information
            log_message = f"User: {user} - Path: {path} - Method: {request.method}"
            self.logger.info(log_message)
            
        except Exception as e:
            # Log any errors in logging (meta-logging)
            self.logger.error(f"Error in request logging: {str(e)}")


class RestrictAccessByTimeMiddleware(MiddlewareMixin):
    """
    Middleware that restricts access to the messaging app during certain hours of the day.
    Denies access by returning 403 Forbidden if accessed outside 9PM and 6PM.
    """
    
    def __init__(self, get_response=None):
        """
        Initialize the middleware.
        """
        self.get_response = get_response
        # Define restricted hours: outside 9PM (21:00) and 6PM (18:00)
        # This means access is restricted from 9PM to 6AM (overnight)
        self.restricted_start = time(21, 0)  # 9:00 PM
        self.restricted_end = time(6, 0)     # 6:00 AM
        
    def __call__(self, request):
        """
        Process the request and check if access should be restricted based on time.
        """
        # Get current server time
        current_time = datetime.now().time()
        
        # Check if current time is within restricted hours
        if self.is_restricted_time(current_time):
            # Check if the request is for the messaging app
            if self.is_messaging_app_request(request):
                return self.get_restricted_response(request)
        
        # If not restricted or not a messaging app request, proceed normally
        response = self.get_response(request)
        return response
    
    def is_restricted_time(self, current_time):
        """
        Check if the current time is within restricted hours.
        Restricted from 9PM to 6AM (overnight).
        """
        if self.restricted_start <= self.restricted_end:
            # Normal case: restricted period doesn't cross midnight
            return self.restricted_start <= current_time <= self.restricted_end
        else:
            # Restricted period crosses midnight (9PM to 6AM)
            return current_time >= self.restricted_start or current_time <= self.restricted_end
    
    def is_messaging_app_request(self, request):
        """
        Check if the request is for the messaging app.
        You can customize this method to match your specific URL patterns.
        """
        # Check if the request path starts with common messaging app paths
        messaging_paths = [
            '/api/conversations/',
            '/api/messages/',
            '/chats/',
            '/messaging/',
            # Add other paths that belong to your messaging app
        ]
        
        # Check if the request path matches any messaging app paths
        return any(request.path.startswith(path) for path in messaging_paths)
    
    def get_restricted_response(self, request):
        """
        Return a 403 Forbidden response with a custom message.
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        message = f"""
        <html>
        <head>
            <title>Access Restricted</title>
            <style>
                body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
                .container {{ max-width: 500px; margin: 0 auto; padding: 20px; border: 1px solid #ccc; border-radius: 10px; }}
                h1 {{ color: #d9534f; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🔒 Access Restricted</h1>
                <p>The messaging service is currently unavailable.</p>
                <p><strong>Service Hours:</strong> 6:00 AM - 9:00 PM</p>
                <p><strong>Current Time:</strong> {current_time}</p>
                <p>Please try again during service hours.</p>
            </div>
        </body>
        </html>
        """
        return HttpResponseForbidden(message)


# Alternative simpler implementation for specific time restriction
class SimpleTimeRestrictionMiddleware(MiddlewareMixin):
    """
    Simplified version that restricts all access during certain hours.
    """
    
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.restricted_start = time(21, 0)  # 9:00 PM
        self.restricted_end = time(6, 0)     # 6:00 AM
    
    def __call__(self, request):
        current_time = datetime.now().time()
        
        # Check if current time is within restricted hours
        if self.restricted_start <= self.restricted_end:
            is_restricted = self.restricted_start <= current_time <= self.restricted_end
        else:
            is_restricted = current_time >= self.restricted_start or current_time <= self.restricted_end
        
        if is_restricted:
            return HttpResponseForbidden(
                "Access to this service is restricted between 9:00 PM and 6:00 AM. "
                "Please try again during service hours."
            )
        
        return self.get_response(request)