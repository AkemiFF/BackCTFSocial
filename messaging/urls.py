from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (AttachmentViewSet, ChannelMemberViewSet, ChannelViewSet,
                    MessageViewSet, ReadReceiptViewSet)

router = DefaultRouter()
router.register(r'channels', ChannelViewSet, basename='channel')
router.register(r'members', ChannelMemberViewSet, basename='channel-member')
router.register(r'messages', MessageViewSet, basename='message')
router.register(r'read-receipts', ReadReceiptViewSet, basename='read-receipt')
router.register(r'attachments', AttachmentViewSet, basename='attachment')

urlpatterns = [
    path('', include(router.urls)),
]