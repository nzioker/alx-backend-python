from rest_framework import permissions

class IsParticipantOfConversation(permissions.BasePermission):
    """
    Custom permission to only allow participants of a conversation to access it.
    """
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'participants_id'):
            return obj.participants_id == request.user
        elif hasattr(obj, 'conversation_id'):
            return obj.conversation_id.participants_id == request.user
        return False

class IsMessageSenderOrParticipant(permissions.BasePermission):
    """
    Custom permission to only allow message sender or conversation participant to access messages.
    """
    def has_object_permission(self, request, view, obj):
        return obj.sender_id == request.user or obj.conversation_id.participants_id == request.user