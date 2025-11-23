import os
import logging
from datetime import datetime
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings

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