from rest_framework import serializers
from .models import AIConversation, AIMessage, AIInsight, AIUsageLog


class AIMessageSerializer(serializers.ModelSerializer):
    """Serializer for AIMessage model"""
    class Meta:
        model = AIMessage
        fields = ['id', 'role', 'text', 'created_at']
        read_only_fields = ['id', 'created_at']


class AIConversationSerializer(serializers.ModelSerializer):
    """Serializer for AIConversation model"""
    messages = AIMessageSerializer(many=True, read_only=True)
    message_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AIConversation
        fields = [
            'id', 'title', 'message_count', 'messages',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_message_count(self, obj):
        return obj.messages.count()


class AIConversationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating conversations"""
    class Meta:
        model = AIConversation
        fields = ['title']
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AIChatRequestSerializer(serializers.Serializer):
    """Serializer for AI chat requests"""
    conversation_id = serializers.UUIDField(required=False, allow_null=True)
    message = serializers.CharField(required=True, max_length=2000)
    context = serializers.JSONField(required=False, default=dict)


class AIChatResponseSerializer(serializers.Serializer):
    """Serializer for AI chat responses"""
    conversation_id = serializers.UUIDField()
    message = AIMessageSerializer()
    response = AIMessageSerializer()
    insights = serializers.ListField(required=False)


class AIInsightSerializer(serializers.ModelSerializer):
    """Serializer for AIInsight model"""
    class Meta:
        model = AIInsight
        fields = [
            'id', 'insight_type', 'title', 'description', 'priority',
            'is_read', 'is_dismissed', 'action_url', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AIInsightCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating insights"""
    class Meta:
        model = AIInsight
        fields = [
            'insight_type', 'title', 'description', 'priority',
            'action_url', 'metadata'
        ]
    
    def create(self, validated_data):
        validated_data['user'] = self.context['request'].user
        return super().create(validated_data)


class AIUsageLogSerializer(serializers.ModelSerializer):
    """Serializer for AIUsageLog model"""
    class Meta:
        model = AIUsageLog
        fields = [
            'id', 'endpoint', 'tokens_used', 'response_time_ms',
            'success', 'error_message', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class AIUsageSummarySerializer(serializers.Serializer):
    """Serializer for AI usage summary"""
    total_requests = serializers.IntegerField()
    total_tokens = serializers.IntegerField()
    avg_response_time = serializers.FloatField()
    success_rate = serializers.FloatField()
    requests_by_endpoint = serializers.DictField()
    daily_usage = serializers.ListField()


class FinancialAnalysisSerializer(serializers.Serializer):
    """Serializer for financial analysis requests"""
    analysis_type = serializers.ChoiceField(
        choices=[
            ('SPENDING_SUMMARY', 'Spending Summary'),
            ('BUDGET_ANALYSIS', 'Budget Analysis'),
            ('SAVINGS_RECOMMENDATIONS', 'Savings Recommendations'),
            ('DEBT_PAYOFF', 'Debt Payoff Strategy'),
            ('INVESTMENT_ADVICE', 'Investment Advice'),
            ('TAX_OPTIMIZATION', 'Tax Optimization'),
        ]
    )
    period = serializers.CharField(max_length=20, default='month')
    include_projections = serializers.BooleanField(default=False)


class NaturalLanguageSearchSerializer(serializers.Serializer):
    """Serializer for natural language search"""
    query = serializers.CharField(max_length=500, required=True)
    limit = serializers.IntegerField(default=20, min_value=1, max_value=100)