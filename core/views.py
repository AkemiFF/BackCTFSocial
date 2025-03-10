# core/views.py
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Audit, Category, Feedback, Setting, Skill, Tag
from .permissions import IsAdminOrReadOnly, IsAdminUser, IsOwnerOrAdmin
from .serializers import (AuditSerializer, CategorySerializer,
                          FeedbackSerializer, SettingSerializer,
                          SkillSerializer, TagSerializer)


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    lookup_field = 'slug'


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'])
    def root(self, request):
        """Get only root categories (those without a parent)."""
        root_categories = Category.objects.filter(parent=None)
        serializer = self.get_serializer(root_categories, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, slug=None):
        """Get direct children of a category."""
        category = self.get_object()
        children = Category.objects.filter(parent=category)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)


class SkillViewSet(viewsets.ModelViewSet):
    queryset = Skill.objects.all()
    serializer_class = SkillSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['skill_type', 'parent']
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    lookup_field = 'slug'
    
    @action(detail=False, methods=['get'])
    def root(self, request):
        """Get only root skills (those without a parent)."""
        root_skills = Skill.objects.filter(parent=None)
        serializer = self.get_serializer(root_skills, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def children(self, request, slug=None):
        """Get direct children of a skill."""
        skill = self.get_object()
        children = Skill.objects.filter(parent=skill)
        serializer = self.get_serializer(children, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def related(self, request, slug=None):
        """Get related skills."""
        skill = self.get_object()
        related = skill.related_skills.all()
        serializer = self.get_serializer(related, many=True)
        return Response(serializer.data)


class SettingViewSet(viewsets.ModelViewSet):
    serializer_class = SettingSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_public']
    search_fields = ['key', 'description']
    lookup_field = 'key'
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return Setting.objects.all()
        return Setting.objects.filter(is_public=True)


class FeedbackViewSet(viewsets.ModelViewSet):
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['feedback_type', 'status']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'status']
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.role == 'administrator':
            return Feedback.objects.all()
        return Feedback.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        """Mark feedback as resolved."""
        feedback = self.get_object()
        
        # Only admins can resolve feedback
        if not (request.user.is_staff or request.user.role == 'administrator'):
            return Response(
                {"detail": "You do not have permission to resolve feedback."}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        notes = request.data.get('notes', '')
        feedback.resolve(notes)
        
        serializer = self.get_serializer(feedback)
        return Response(serializer.data)


class AuditViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['action', 'entity_type', 'user']
    search_fields = ['description', 'entity_id']
    ordering_fields = ['timestamp']
    
    def get_queryset(self):
        return Audit.objects.all()
    
    @action(detail=False, methods=['get'])
    def my_activity(self, request):
        """Get the current user's activity log."""
        logs = Audit.objects.filter(user=request.user).order_by('-timestamp')
        page = self.paginate_queryset(logs)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(logs, many=True)
        return Response(serializer.data)