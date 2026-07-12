from rest_framework import serializers
from decimal import Decimal
from .models import SpendingHeatmap, FinancialScore, ExpenseForecast, MonthlyReport, CategoryTrend


class SpendingHeatmapSerializer(serializers.ModelSerializer):
    """Serializer for spending heatmap"""
    class Meta:
        model = SpendingHeatmap
        fields = [
            'id', 'date', 'total_spent', 'transaction_count',
            'category_breakdown', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class FinancialScoreSerializer(serializers.ModelSerializer):
    """Serializer for financial score"""
    grade = serializers.SerializerMethodField()
    
    class Meta:
        model = FinancialScore
        fields = [
            'id', 'overall_score', 'savings_score', 'budgeting_score',
            'debt_score', 'investment_score', 'grade', 'insights',
            'calculated_at'
        ]
        read_only_fields = ['id', 'calculated_at']
    
    def get_grade(self, obj):
        """Get letter grade based on score"""
        if obj.overall_score >= 90:
            return 'A+'
        elif obj.overall_score >= 80:
            return 'A'
        elif obj.overall_score >= 70:
            return 'B'
        elif obj.overall_score >= 60:
            return 'C'
        elif obj.overall_score >= 50:
            return 'D'
        else:
            return 'F'


class ExpenseForecastSerializer(serializers.ModelSerializer):
    """Serializer for expense forecast"""
    class Meta:
        model = ExpenseForecast
        fields = [
            'id', 'forecast_date', 'predicted_amount', 'confidence_score',
            'category_breakdown', 'model_version', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class MonthlyReportSerializer(serializers.ModelSerializer):
    """Serializer for monthly reports"""
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = MonthlyReport
        fields = [
            'id', 'report_type', 'title', 'start_date', 'end_date',
            'file', 'file_url', 'file_format', 'data', 'is_generated',
            'generated_at', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_file_url(self, obj):
        """Get file URL if exists"""
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None


class CategoryTrendSerializer(serializers.ModelSerializer):
    """Serializer for category trends"""
    trend_direction = serializers.SerializerMethodField()
    
    class Meta:
        model = CategoryTrend
        fields = [
            'id', 'category', 'period', 'amount', 'transaction_count',
            'percentage_of_total', 'change_from_previous', 'trend_direction',
            'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_trend_direction(self, obj):
        """Get trend direction"""
        if obj.change_from_previous > 0:
            return 'UP'
        elif obj.change_from_previous < 0:
            return 'DOWN'
        else:
            return 'STABLE'


class AnalyticsDashboardSerializer(serializers.Serializer):
    """Serializer for analytics dashboard"""
    total_spent_this_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_spent_last_month = serializers.DecimalField(max_digits=15, decimal_places=2)
    month_over_month_change = serializers.DecimalField(max_digits=5, decimal_places=2)
    top_categories = CategoryTrendSerializer(many=True)
    recent_heatmap = SpendingHeatmapSerializer(many=True)
    financial_score = FinancialScoreSerializer()
    forecast = ExpenseForecastSerializer()
    category_trends = CategoryTrendSerializer(many=True)
    budget_health = serializers.DictField()
    year_over_year = serializers.DictField()


class SpendingPatternSerializer(serializers.Serializer):
    """Serializer for spending patterns"""
    pattern_type = serializers.CharField()
    description = serializers.CharField()
    frequency = serializers.CharField()
    average_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    total_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    occurrences = serializers.IntegerField()
    first_occurrence = serializers.DateField()
    last_occurrence = serializers.DateField()
    confidence = serializers.DecimalField(max_digits=5, decimal_places=2)


class BudgetHealthSerializer(serializers.Serializer):
    """Serializer for budget health"""
    total_budgets = serializers.IntegerField()
    on_track_budgets = serializers.IntegerField()
    at_risk_budgets = serializers.IntegerField()
    over_budget = serializers.IntegerField()
    health_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    recommendations = serializers.ListField(child=serializers.CharField())
    category_breakdown = serializers.ListField(required=False)


class YearOverYearComparisonSerializer(serializers.Serializer):
    """Serializer for year-over-year comparison"""
    current_year_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    previous_year_total = serializers.DecimalField(max_digits=15, decimal_places=2)
    change_amount = serializers.DecimalField(max_digits=15, decimal_places=2)
    change_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    by_category = serializers.DictField()
    by_month = serializers.DictField()