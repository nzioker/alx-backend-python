from rest_framework import permissions

class IsAuthenticated(permissions.BasePermission):
    """
    Custom permission to only allow authenticated users to access the API.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    Allow only participants in a conversation to send, view, update and delete messages.
    """
    
    def has_permission(self, request, view):
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # For list/create actions, check if user can access the endpoint
        if view.action in ['list', 'create']:
            return True
            
        # For other actions, object-level permission will be checked in has_object_permission
        return True

    def has_object_permission(self, request, view, obj):
        """
        Check if the user has permission to access the specific object.
        """
        # Check if user is authenticated
        if not request.user or not request.user.is_authenticated:
            return False
            
        # Handle Conversation objects
        if hasattr(obj, 'participants_id'):
            is_participant = obj.participants_id == request.user
            
            # For safe methods (GET, HEAD, OPTIONS), allow if participant
            if request.method in permissions.SAFE_METHODS:
                return is_participant
                
            # For write methods (POST, PUT, PATCH, DELETE), allow if participant
            elif request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                return is_participant
                
        # Handle Message objects
        elif hasattr(obj, 'conversation_id'):
            is_participant = obj.conversation_id.participants_id == request.user
            is_sender = obj.sender_id == request.user
            
            if request.method in permissions.SAFE_METHODS:
                return is_participant
                
            elif request.method in ['PUT', 'PATCH', 'DELETE']:
                return is_sender and is_participant
                
            elif request.method == 'POST':
                return is_participant
                
        return False

class IsMessageSenderOrParticipant(permissions.BasePermission):
    """
    Custom permission to only allow message sender or conversation participant to access messages.
    Specifically handles PUT, PATCH, DELETE methods for messages.
    """
    
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        """
        Object-level permission for message operations.
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        is_participant = obj.conversation_id.participants_id == request.user
        is_sender = obj.sender_id == request.user
        
        if request.method in permissions.SAFE_METHODS:
            return is_participant
            
        elif request.method in ['PUT', 'PATCH', 'DELETE']:
            return is_sender and is_participant
            
        elif request.method == 'POST':
            return is_participant
            
        return False

class CanSendMessage(permissions.BasePermission):
    """
    Permission to check if user can send messages to a conversation.
    """
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)
        
    def has_object_permission(self, request, view, obj):
        """
        Check if user can send messages to this conversation.
        """
        if not request.user or not request.user.is_authenticated:
            return False
            
        return obj.participants_id == request.user