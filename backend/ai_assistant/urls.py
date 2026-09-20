from django.urls import path

from . import views

urlpatterns = [
    path("chat/", views.chat_view, name="ai-chat"),
    path("config/", views.config_view, name="ai-config"),
    path("sessions/", views.session_list_view, name="ai-session-list"),
    path("sessions/<uuid:session_id>/", views.session_detail_view, name="ai-session-detail"),
]
