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
from .permissions import IsParticipantOfConversation, IsMessageSenderOrParticipant

class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating conversations
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['participants_id__first_name', 'participants_id__last_name']
    ordering_fields = ['created_at']
    filterset_fields = ['participants_id']
    
    def get_queryset(self):
        """Return conversations where the current user is the participant"""
        return Conversation.objects.filter(participants_id=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversation = Conversation.objects.create(
            participants_id=serializer.validated_data['participants_id']
        )
        
        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        conversation = get_object_or_404(Conversation, pk=pk, participants_id=request.user)
        
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating messages
    """
    permission_classes = [IsAuthenticated, IsMessageSenderOrParticipant]
    serializer_class = MessageDetailSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['message_body', 'sender_id__first_name', 'sender_id__last_name']
    ordering_fields = ['sent_at', 'sender_id']
    filterset_fields = ['conversation_id', 'sender_id']
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation_id__participants_id=self.request.user
        ).order_by('-sent_at')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MessageSerializer
        return MessageDetailSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversation = get_object_or_404(
            Conversation, 
            pk=serializer.validated_data['conversation_id'].conversation_id,
            participants_id=request.user
        )
        
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)