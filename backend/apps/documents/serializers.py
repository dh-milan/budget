from rest_framework import serializers
from .models import Document, DocumentTag


class DocumentTagSerializer(serializers.ModelSerializer):
    """Serializer for document tags"""
    class Meta:
        model = DocumentTag
        fields = ['id', 'name', 'color', 'created_at']
        read_only_fields = ['id', 'created_at']


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for documents"""
    tags_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        write_only=True,
        help_text="List of tag names"
    )
    tags = DocumentTagSerializer(many=True, read_only=True)
    file_size_mb = serializers.SerializerMethodField()
    transaction_title = serializers.CharField(source='transaction.title', read_only=True)
    
    class Meta:
        model = Document
        fields = [
            'id', 'title', 'document_type', 'file', 'file_type', 'file_size',
            'file_size_mb', 'description', 'tags', 'tags_list',
            'transaction', 'transaction_title', 'is_cloud_synced',
            'uploaded_at', 'updated_at'
        ]
        read_only_fields = ['id', 'uploaded_at', 'updated_at']
    
    def get_file_size_mb(self, obj):
        """Convert file size to MB"""
        return round(obj.file_size / (1024 * 1024), 2)
    
    def create(self, validated_data):
        """Create document with tags"""
        tags_data = validated_data.pop('tags_list', [])
        document = Document.objects.create(**validated_data)
        
        # Get or create tags
        for tag_name in tags_data:
            tag, _ = DocumentTag.objects.get_or_create(
                user=validated_data['user'],
                name=tag_name
            )
            document.tags.add(tag)
        
        return document
    
    def update(self, instance, validated_data):
        """Update document and tags"""
        tags_data = validated_data.pop('tags_list', None)
        
        # Update document fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update tags if provided
        if tags_data is not None:
            instance.tags.clear()
            for tag_name in tags_data:
                tag, _ = DocumentTag.objects.get_or_create(
                    user=instance.user,
                    name=tag_name
                )
                instance.tags.add(tag)
        
        return instance


class DocumentSearchSerializer(serializers.Serializer):
    """Serializer for document search"""
    query = serializers.CharField(required=False, help_text="Search in title and description")
    document_type = serializers.ChoiceField(
        choices=Document.DOCUMENT_TYPES,
        required=False
    )
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False,
        help_text="Filter by tag names"
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    has_transaction = serializers.BooleanField(required=False)
    is_cloud_synced = serializers.BooleanField(required=False)


class DocumentStatsSerializer(serializers.Serializer):
    """Serializer for document statistics"""
    total_documents = serializers.IntegerField()
    total_size_mb = serializers.FloatField()
    by_type = serializers.DictField()
    by_month = serializers.DictField()
    cloud_synced_count = serializers.IntegerField()
    pending_sync_count = serializers.IntegerField()