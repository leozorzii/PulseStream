from rest_framework import serializers
from apps.stream_core.models import ContentSource

class ContentSourceSerializer(serializers.ModelSerializer):
    """Serializa objetos ContentSource para JSON e vice-versa."""
    class Meta:
        #qual model serializer traduzir
        model = ContentSource
        #campos que vao pro JSON na web
        fields = ["id", "name", "plataform", "external_id", "is_active", "created_at"] 