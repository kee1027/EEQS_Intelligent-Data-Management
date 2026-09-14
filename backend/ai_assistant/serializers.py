from rest_framework import serializers

from .models import AiChatMessage, AiChatSession


class AiChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatMessage
        fields = ["id", "role", "content", "created_at"]


class AiChatSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatSession
        fields = ["id", "title", "created_at", "updated_at"]


class AiChatSessionDetailSerializer(serializers.ModelSerializer):
    messages = AiChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = AiChatSession
        fields = ["id", "title", "created_at", "updated_at", "messages"]
