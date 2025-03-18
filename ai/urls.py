from django.urls import include, path

from .views import chat_stream, generate_module

urlpatterns = [
    path('stream/', chat_stream, name='chat_stream'),
    path("generate-module/", generate_module, name="generate_module"),
]