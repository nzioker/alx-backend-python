import os
import logging
from datetime import datetime, time, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from collections import defaultdict
import threading

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


class OffensiveLanguageMiddleware(MiddlewareMixin):
    """
    Middleware that limits the number of chat messages a user can send within a certain time window
    based on their IP address. Limits to 5 messages per minute per IP.
    """
    
    def __init__(self, get_response=None):
        """
        Initialize the middleware with rate limiting settings.
        """
        self.get_response = get_response
        
        # Rate limiting configuration
        self.message_limit = 5  # Maximum messages per time window
        self.time_window = 60   # Time window in seconds (1 minute)
        
        # Thread-safe storage for IP request counts
        self.ip_requests = defaultdict(list)
        self.lock = threading.Lock()
        
        # Paths that should be rate limited (messaging endpoints)
        self.rate_limited_paths = [
            '/api/messages/',
            '/api/conversations/',
            '/chats/send_message/',
            # Add other messaging endpoints that should be rate limited
        ]
    
    def __call__(self, request):
        """
        Process the request and apply rate limiting for messaging endpoints.
        """
        # Check if this is a POST request to a rate-limited messaging endpoint
        if (request.method == 'POST' and 
            self.is_rate_limited_path(request.path)):
            
            # Get client IP address
            ip_address = self.get_client_ip(request)
            
            # Check rate limit for this IP
            if self.is_rate_limited(ip_address):
                return self.get_rate_limit_response(ip_address)
            
            # If not rate limited, track the request
            self.track_request(ip_address)
        
        # Proceed with the request
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
        """
        Extract the client IP address from the request.
        Handles various proxy scenarios.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # In case of multiple proxies, take the first IP
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', '0.0.0.0')
        return ip
    
    def is_rate_limited_path(self, path):
        """
        Check if the request path should be rate limited.
        """
        return any(path.startswith(rate_path) for rate_path in self.rate_limited_paths)
    
    def is_rate_limited(self, ip_address):
        """
        Check if the IP address has exceeded the rate limit.
        """
        with self.lock:
            now = datetime.now()
            
            # Clean old requests outside the time window
            self.clean_old_requests(ip_address, now)
            
            # Check if current requests exceed the limit
            current_requests = self.ip_requests[ip_address]
            return len(current_requests) >= self.message_limit
    
    def track_request(self, ip_address):
        """
        Track a new request from the IP address.
        """
        with self.lock:
            now = datetime.now()
            self.ip_requests[ip_address].append(now)
    
    def clean_old_requests(self, ip_address, current_time):
        """
        Remove requests that are outside the current time window.
        """
        if ip_address in self.ip_requests:
            # Calculate the cutoff time
            cutoff_time = current_time - timedelta(seconds=self.time_window)
            
            # Filter out old requests
            self.ip_requests[ip_address] = [
                req_time for req_time in self.ip_requests[ip_address]
                if req_time > cutoff_time
            ]
            
            # Remove IP if no recent requests
            if not self.ip_requests[ip_address]:
                del self.ip_requests[ip_address]
    
    def get_rate_limit_response(self, ip_address):
        """
        Return a 429 Too Many Requests response when rate limit is exceeded.
        """
        with self.lock:
            # Get current request count and reset time
            current_requests = self.ip_requests.get(ip_address, [])
            request_count = len(current_requests)
            
            if current_requests:
                # Find the oldest request to calculate reset time
                oldest_request = min(current_requests)
                reset_time = oldest_request + timedelta(seconds=self.time_window)
                seconds_remaining = (reset_time - datetime.now()).total_seconds()
                seconds_remaining = max(0, int(seconds_remaining))
            else:
                seconds_remaining = self.time_window
        
        response_data = {
            "error": "Rate limit exceeded",
            "message": f"Too many messages sent. Limit is {self.message_limit} messages per minute.",
            "limit": self.message_limit,
            "time_window_seconds": self.time_window,
            "current_requests": request_count,
            "retry_after_seconds": seconds_remaining,
            "retry_after_time": datetime.now() + timedelta(seconds=seconds_remaining)
        }
        
        response = JsonResponse(response_data, status=429)
        response['Retry-After'] = seconds_remaining
        return response
    
    def get_rate_limit_info(self, ip_address):
        """
        Get current rate limit information for an IP address (for debugging/monitoring).
        """
        with self.lock:
            current_requests = self.ip_requests.get(ip_address, [])
            request_count = len(current_requests)
            remaining = max(0, self.message_limit - request_count)
            
            if current_requests:
                reset_time = min(current_requests) + timedelta(seconds=self.time_window)
                seconds_remaining = (reset_time - datetime.now()).total_seconds()
                seconds_remaining = max(0, int(seconds_remaining))
            else:
                seconds_remaining = 0
            
            return {
                "ip_address": ip_address,
                "current_requests": request_count,
                "remaining_requests": remaining,
                "limit": self.message_limit,
                "time_window_seconds": self.time_window,
                "reset_in_seconds": seconds_remaining
            }

