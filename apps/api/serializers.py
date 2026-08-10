from rest_framework import serializers
from apps.stream_core.models import ContentSource, RawPost

class ContentSourceSerializer(serializers.ModelSerializer):
    """Serializa objetos ContentSource para JSON e vice-versa."""
    class Meta:
        #qual model serializer traduzir
        model = ContentSource
        #campos que vao pro JSON na web
        fields = ["id", "name", "plataform", "external_id", "is_active", "created_at"] 
        
        
class RawPostSerializer(serializers.ModelSerializer):
    """Serializa objetos RawPost para JSON e vice-versa"""
    class Meta:
        model = RawPost
        fields = ["id", "source", "external_id", "text_content", "published_at", "is_processed"]