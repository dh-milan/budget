from rest_framework import serializers
from decimal import Decimal
from .models import Account, Transaction, Category, Attachment


class AccountSerializer(serializers.ModelSerializer):
    """Serializer for Account model"""
    class Meta:
        model = Account
        fields = [
            'id', 'name', 'type', 'balance', 'currency',
            'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AccountCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating accounts"""
    class Meta:
        model = Account
        fields = ['name', 'type', 'currency', 'initial_balance']
    
    def create(self, validated_data):
        initial_balance = validated_data.pop('initial_balance', Decimal('0.00'))
        account = Account.objects.create(**validated_data, balance=initial_balance)
        return account


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer for Transaction model"""
    account_name = serializers.CharField(source='account.name', read_only=True)
    account_type = serializers.CharField(source='account.type', read_only=True)
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'account', 'account_name', 'account_type', 'title', 'amount',
            'category', 'type', 'timestamp', 'note', 'tags',
            'is_recurring', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class TransactionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating transactions with account balance update"""
    class Meta:
        model = Transaction
        fields = [
            'account', 'title', 'amount', 'category', 'type',
            'timestamp', 'note', 'tags', 'is_recurring'
        ]
    
    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero")
        return value
    
    def validate_timestamp(self, value):
        from django.utils import timezone
        if value > timezone.now():
            raise serializers.ValidationError("Transaction timestamp cannot be in the future")
        return value


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'type', 'color', 'icon',
            'parent', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating categories"""
    class Meta:
        model = Category
        fields = ['name', 'type', 'color', 'icon', 'parent']


class AttachmentSerializer(serializers.ModelSerializer):
    """Serializer for Attachment model"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Attachment
        fields = [
            'id', 'transaction', 'file', 'file_url', 'file_type',
            'file_size', 'uploaded_at'
        ]
        read_only_fields = ['id', 'uploaded_at']
    
    def get_file_url(self, obj):
        request = self.context.get('request')
        if obj.file and request:
            return request.build_absolute_uri(obj.file.url)
        return None


class BulkTransactionCreateSerializer(serializers.Serializer):
    """Serializer for bulk transaction creation"""
    transactions = TransactionCreateSerializer(many=True)
    
    def validate_transactions(self, value):
        if not value:
            raise serializers.ValidationError("At least one transaction is required")
        if len(value) > 100:
            raise serializers.ValidationError("Cannot create more than 100 transactions at once")
        return value


class TransactionSummarySerializer(serializers.Serializer):
    """Serializer for transaction summary statistics"""
    total_income = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_expenses = serializers.DecimalField(max_digits=15, decimal_places=2)
    net_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    transaction_count = serializers.IntegerField()
    category_breakdown = serializers.DictField()
    date_range = serializers.DictField()


class AccountBalanceSerializer(serializers.Serializer):
    """Serializer for account balance information"""
    account_id = serializers.UUIDField()
    account_name = serializers.CharField()
    account_type = serializers.CharField()
    balance = serializers.DecimalField(max_digits=15, decimal_places=2)
    currency = serializers.CharField()
    transaction_count = serializers.IntegerField()