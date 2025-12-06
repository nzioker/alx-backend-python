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
from .permissions import IsParticipantOfConversation, IsMessageSenderOrParticipant, CanSendMessage
from .pagination import MessagePagination, ConversationPagination
from .filters import MessageFilter, ConversationFilter
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from messaging.models import Message


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating conversations
    """
    permission_classes = [IsAuthenticated, IsParticipantOfConversation]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['participants_id__first_name', 'participants_id__last_name']
    ordering_fields = ['created_at', 'participants_id__first_name']
    filterset_class = ConversationFilter
    pagination_class = ConversationPagination
    
    def get_queryset(self):
        """Return conversations where the current user is the participant"""
        return Conversation.objects.filter(participants_id=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return ConversationCreateSerializer
        return ConversationSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List conversations with pagination and filtering
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        conversation = Conversation.objects.create(
            participants_id=serializer.validated_data['participants_id']
        )
        
        response_serializer = ConversationSerializer(conversation)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsParticipantOfConversation().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsParticipantOfConversation().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You do not have permission to perform this action."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanSendMessage])
    def send_message(self, request, pk=None):
        conversation = get_object_or_404(Conversation, pk=pk)
        
        if not CanSendMessage().has_object_permission(request, self, conversation):
            return Response(
                {"detail": "You do not have permission to send messages to this conversation."},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = MessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = Message.objects.create(
            sender_id=request.user,
            conversation_id=conversation,
            message_body=serializer.validated_data['message_body']
        )
        
        response_serializer = MessageDetailSerializer(message)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['get'])
    def messages(self, request, pk=None):
        """
        Get all messages for a specific conversation with pagination and filtering
        """
        conversation = get_object_or_404(Conversation, pk=pk, participants_id=request.user)
        messages = conversation.messages.all().order_by('sent_at')
        
        # Apply filtering to messages
        message_filter = MessageFilter(request.GET, queryset=messages)
        filtered_messages = message_filter.qs
        
        # Apply pagination
        paginator = MessagePagination()
        paginated_messages = paginator.paginate_queryset(filtered_messages, request)
        
        serializer = MessageDetailSerializer(paginated_messages, many=True)
        return paginator.get_paginated_response(serializer.data)

class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for listing and creating messages with pagination and filtering
    """
    permission_classes = [IsAuthenticated, IsMessageSenderOrParticipant]
    serializer_class = MessageDetailSerializer
    pagination_class = MessagePagination
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['message_body', 'sender_id__first_name', 'sender_id__last_name']
    ordering_fields = ['sent_at', 'sender_id__first_name']
    filterset_class = MessageFilter
    
    def get_queryset(self):
        return Message.objects.filter(
            conversation_id__participants_id=self.request.user
        ).order_by('-sent_at')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return MessageSerializer
        return MessageDetailSerializer
    
    def list(self, request, *args, **kwargs):
        """
        List messages with pagination and filtering
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
            
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
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
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsMessageSenderOrParticipant().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You can only edit your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsMessageSenderOrParticipant().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You can only edit your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if not IsMessageSenderOrParticipant().has_object_permission(request, self, instance):
            return Response(
                {"detail": "You can only delete your own messages."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)
    
    @action(detail=False, methods=['get'])
    def my_messages(self, request):
        """
        Get all messages sent by the current user with pagination and filtering
        """
        messages = Message.objects.filter(sender_id=request.user).order_by('-sent_at')
        
        # Apply filtering
        message_filter = MessageFilter(request.GET, queryset=messages)
        filtered_messages = message_filter.qs
        
        # Apply pagination
        paginator = MessagePagination()
        paginated_messages = paginator.paginate_queryset(filtered_messages, request)
        
        serializer = self.get_serializer(paginated_messages, many=True)
        return paginator.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """
        Get recent messages (last 10) for the current user
        """
        messages = self.get_queryset()[:10]
        serializer = self.get_serializer(messages, many=True)
        return Response(serializer.data)
    

@method_decorator(cache_page(60), name='dispatch')
class ConversationListView(ListView):
    """Cached view for displaying conversation list"""
    model = Message
    template_name = 'messaging/conversation_list.html'
    context_object_name = 'messages'
    
    def get_queryset(self):
        return Message.objects.filter(
            receiver=self.request.user
        ).select_related('sender').order_by('-timestamp')