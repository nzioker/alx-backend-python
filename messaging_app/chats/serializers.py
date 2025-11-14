from rest_framework import serializers
from .models import User, Message, Conversation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['role','email','password_hash','phone_number']
        read_only_fields = ['user_id', 'created_at']

class ConversationSerializer(serializers.ModelSerializer):
    participant = UserSerializer(source='participants_id', read_only=True)
    
    class Meta:
        model = Conversation
        fields = [
            'conversation_id',
            'participants_id',  
            'participant',      
            'created_at'
        ]
        read_only_fields = ['conversation_id', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    
    sender = UserSerializer(source='sender_id', read_only=True)
    conversation = ConversationSerializer(source='conversation_id', read_only=True)
    
    class Meta:
        model = Message
        fields = [
            'message_id',
            'sender_id',        
            'sender',           
            'conversation_id',  
            'conversation',     
            'message_body',
            'sent_at'
        ]
        read_only_fields = ['message_id', 'sent_at']