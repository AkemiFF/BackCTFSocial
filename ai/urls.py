from django.urls import include, path

from .views import chat_stream

urlpatterns = [
    path('stream/', chat_stream, name='chat_stream'),
]