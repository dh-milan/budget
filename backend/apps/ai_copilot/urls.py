from django.urls import path
from .views import (
    AIChatView,
    AIConversationListView,
    AIConversationDetailView,
    AIInsightListView,
    AIInsightDetailView,
    AIUsageSummaryView,
    FinancialAnalysisView,
    NaturalLanguageSearchView,
)

urlpatterns = [
    # AI Chat
    path('chat/', AIChatView.as_view(), name='ai-chat'),
    
    # Conversations
    path('conversations/', AIConversationListView.as_view(), name='conversation-list'),
    path('conversations/<uuid:conversation_id>/', AIConversationDetailView.as_view(), name='conversation-detail'),
    
    # Insights
    path('insights/', AIInsightListView.as_view(), name='insight-list'),
    path('insights/<uuid:insight_id>/', AIInsightDetailView.as_view(), name='insight-detail'),
    
    # Usage and Analytics
    path('usage/', AIUsageSummaryView.as_view(), name='ai-usage'),
    path('analysis/', FinancialAnalysisView.as_view(), name='financial-analysis'),
    
    # Natural Language Search
    path('search/', NaturalLanguageSearchView.as_view(), name='natural-language-search'),
]