from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from .models import User, Conversation, Message
from .serializers import (
    ConversationSerializer, 
    MessageSerializer,
    ConversationCreateSerializer,
    MessageDetailSerializer
)

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating conversations
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['participants_id__first_name', 'participants_id__last_name']
    ordering_fields = ['created_at']
    filterset_fields = ['participants_id']
    
    def get_queryset(self):
        """Return conversations where the current user is the participant"""
        return Conversation.objects.filter(participants_id=self.request.user)
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def list(self, request, *args, **kwargs):
        """List all conversations for the current user"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new conversation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the conversation
        conversation = Conversation.objects.create(
            participants_id=serializer.validated_data['participants_id']
        )
        
        # Return the created conversation with full details
        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """Retrieve a specific conversation with its messages"""
        conversation = get_object_or_404(Conversation, pk=pk, participants_id=request.user)
        serializer = self.get_serializer(conversation)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to an existing conversation"""
        conversation = get_object_or_404(Conversation, pk=pk, participants_id=request.user)
        
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create the message
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        # Return the created message
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """Get all messages for a specific conversation"""
        conversation = get_object_or_404(Conversation, pk=pk, participants_id=request.user)
        messages = conversation.messages.all().order_by('sent_at')
        
        serializer = MessageDetailSerializer(messages, many=True)
        return Response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating messages
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MessageDetailSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['message_body', 'sender_id__first_name', 'sender_id__last_name']
    ordering_fields = ['sent_at', 'sender_id']
    filterset_fields = ['conversation_id', 'sender_id']
    
    def get_queryset(self):
        """Return messages where the current user is either sender or conversation participant"""
        return Message.objects.filter(
            conversation_id__participants_id=self.request.user
        ).order_by('-sent_at')
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action"""
        if self.action in ['create', 'update', 'partial_update']:
            return MessageSerializer
        return MessageDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """List all messages for the current user"""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        """Create a new message in a conversation"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Verify the user has access to the conversation
        conversation = get_object_or_404(
            Conversation, 
            pk=serializer.validated_data['conversation_id'].conversation_id,
            participants_id=request.user
        )
        
        # Create the message
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        # Return the created message with full details
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def retrieve(self, request, pk=None):
        """Retrieve a specific message"""
        message = get_object_or_404(
            Message, 
            pk=pk, 
            conversation_id__participants_id=request.user
        )
        serializer = self.get_serializer(message)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        """Get all messages sent by the current user"""
        messages = Message.objects.filter(sender_id=request.user).order_by('-sent_at')
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent messages (last 10) for the current user"""
        messages = self.get_queryset()[:10]
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)