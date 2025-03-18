from django.urls import include, path

from .views import *

urlpatterns = [
    path('stream/', chat_stream, name='chat_stream'),
    path("generate-module/", generate_module, name="generate_module"),
    path('evaluate-answer/', EvaluateAnswerView.as_view(), name='evaluate-answer'),
]