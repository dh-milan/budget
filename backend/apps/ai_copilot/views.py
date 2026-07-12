import requests
import json
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import datetime, timedelta
from decimal import Decimal

from .models import AIConversation, AIMessage, AIInsight, AIUsageLog
from .serializers import (
    AIConversationSerializer, AIConversationCreateSerializer,
    AIMessageSerializer, AIChatRequestSerializer, AIChatResponseSerializer,
    AIInsightSerializer, AIInsightCreateSerializer,
    AIUsageLogSerializer, AIUsageSummarySerializer,
    FinancialAnalysisSerializer, NaturalLanguageSearchSerializer
)
from apps.authentication.models import AuditLog
from apps.ledger.models import Transaction, Account
from apps.budgeting.models import Budget, SavingsGoal, Debt
from apps.bills.models import Bill


class AIChatView(APIView):
    """AI chat endpoint - main interface for AI conversations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = AIChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        message_text = serializer.validated_data['message']
        conversation_id = serializer.validated_data.get('conversation_id')
        context = serializer.validated_data.get('context', {})
        
        start_time = timezone.now()
        
        try:
            # Get or create conversation
            if conversation_id:
                try:
                    conversation = AIConversation.objects.get(
                        id=conversation_id, 
                        user=request.user
                    )
                except AIConversation.DoesNotExist:
                    return Response(
                        {"error": "Conversation not found"}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                # Create new conversation with auto-generated title
                title = self.generate_conversation_title(message_text)
                conversation = AIConversation.objects.create(
                    user=request.user,
                    title=title
                )
            
            # Save user message
            user_message = AIMessage.objects.create(
                conversation=conversation,
                role='user',
                text=message_text
            )
            
            # Gather user financial context
            financial_context = self.gather_financial_context(request.user)
            
            # Call Gemini AI
            ai_response_text = self.call_gemini_ai(
                user_message=message_text,
                financial_context=financial_context,
                conversation_history=self.get_conversation_history(conversation)
            )
            
            # Save AI response
            ai_message = AIMessage.objects.create(
                conversation=conversation,
                role='model',
                text=ai_response_text
            )
            
            # Update conversation timestamp
            conversation.save()
            
            # Log AI usage
            response_time = int((timezone.now() - start_time).total_seconds() * 1000)
            AIUsageLog.objects.create(
                user=request.user,
                endpoint='ai_chat',
                tokens_used=len(message_text.split()) + len(ai_response_text.split()),
                response_time_ms=response_time,
                success=True
            )
            
            # Generate insights if needed
            insights = self.generate_insights(request.user, message_text, ai_response_text)
            
            response_data = {
                'conversation_id': conversation.id,
                'message': AIMessageSerializer(user_message).data,
                'response': AIMessageSerializer(ai_message).data,
                'insights': AIInsightSerializer(insights, many=True).data if insights else []
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Log failed request
            response_time = int((timezone.now() - start_time).total_seconds() * 1000)
            AIUsageLog.objects.create(
                user=request.user,
                endpoint='ai_chat',
                tokens_used=0,
                response_time_ms=response_time,
                success=False,
                error_message=str(e)
            )
            
            return Response(
                {"error": f"AI request failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def generate_conversation_title(self, message):
        """Generate a title for the conversation based on the first message"""
        # Simple title generation - take first 50 characters
        return message[:50] + ('...' if len(message) > 50 else '')
    
    def get_conversation_history(self, conversation, limit=10):
        """Get recent conversation history"""
        messages = conversation.messages.order_by('-created_at')[:limit]
        return [{'role': msg.role, 'text': msg.text} for msg in reversed(messages)]
    
    def gather_financial_context(self, user):
        """Gather user's financial data for AI context"""
        context = {}
        
        # Get accounts
        accounts = Account.objects.filter(user=user, is_active=True)
        context['accounts'] = [
            {
                'name': acc.name,
                'type': acc.type,
                'balance': str(acc.balance),
                'currency': acc.currency
            }
            for acc in accounts
        ]
        
        # Get recent transactions
        recent_transactions = Transaction.objects.filter(
            account__user=user
        ).order_by('-timestamp')[:20]
        context['recent_transactions'] = [
            {
                'title': tx.title,
                'amount': str(tx.amount),
                'category': tx.category,
                'type': tx.type,
                'date': tx.timestamp.strftime('%Y-%m-%d')
            }
            for tx in recent_transactions
        ]
        
        # Get budgets
        budgets = Budget.objects.filter(user=user, is_active=True)
        context['budgets'] = [
            {
                'category': bud.category,
                'limit': str(bud.limit_amount),
                'spent': str(bud.spent_amount)
            }
            for bud in budgets
        ]
        
        # Get savings goals
        goals = SavingsGoal.objects.filter(user=user, is_active=True)
        context['savings_goals'] = [
            {
                'name': goal.name,
                'target': str(goal.target_amount),
                'current': str(goal.current_amount)
            }
            for goal in goals
        ]
        
        # Get debts
        debts = Debt.objects.filter(user=user, is_active=True)
        context['debts'] = [
            {
                'name': debt.name,
                'type': debt.type,
                'balance': str(debt.total_balance),
                'interest_rate': str(debt.interest_rate)
            }
            for debt in debts
        ]
        
        # Get upcoming bills
        today = timezone.now().date()
        upcoming_bills = Bill.objects.filter(
            user=user,
            is_active=True,
            is_paid=False,
            due_date__gte=today
        ).order_by('due_date')[:10]
        context['upcoming_bills'] = [
            {
                'name': bill.name,
                'amount': str(bill.amount),
                'due_date': bill.due_date.strftime('%Y-%m-%d')
            }
            for bill in upcoming_bills
        ]
        
        return context
    
    def call_gemini_ai(self, user_message, financial_context, conversation_history):
        """Call Gemini AI API with user context"""
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        # Build system prompt
        system_prompt = """You are an elite personal financial advisor with CFA and CFP certifications. 
Your mission is to provide rigorous, accurate, actionable, and mathematically correct financial advice.

STRICT RULES:
1. NEVER invent user transactions or balances. Only use the provided context.
2. Ensure all math calculations are perfect.
3. Keep answers friendly, conversational, and direct.
4. When identifying issues, provide specific actionable suggestions.
5. Format all monetary values with $ and commas for readability.
6. Be concise but thorough - aim for 2-4 paragraphs unless detailed analysis is requested.
7. Use bullet points for lists and recommendations.
"""
        
        # Build user context
        context_text = f"""
User Financial Profile:
- Accounts: {len(financial_context.get('accounts', []))} accounts
- Recent Transactions: {len(financial_context.get('recent_transactions', []))} transactions
- Active Budgets: {len(financial_context.get('budgets', []))} budgets
- Savings Goals: {len(financial_context.get('savings_goals', []))} goals
- Debts: {len(financial_context.get('debts', []))} debts
- Upcoming Bills: {len(financial_context.get('upcoming_bills', []))} bills

Recent Transactions:
"""
        for tx in financial_context.get('recent_transactions', [])[:10]:
            context_text += f"- {tx['date']} | {tx['title']} | {tx['category']} | ${tx['amount']} ({tx['type']})\n"
        
        context_text += "\nBudgets:\n"
        for bud in financial_context.get('budgets', [])[:5]:
            context_text += f"- {bud['category']}: ${bud['limit']} limit, ${bud['spent']} spent\n"
        
        # Build full prompt
        full_prompt = f"{system_prompt}\n\n{context_text}\n\nUser Question: {user_message}\n\nProvide your expert financial advice:"
        
        # Prepare request
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": full_prompt}
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 1024,
            }
        }
        
        # Make request
        response = requests.post(api_url, json=payload, headers=headers, timeout=15)
        response.raise_for_status()
        response_json = response.json()
        
        # Parse response
        ai_text = response_json['candidates'][0]['content']['parts'][0]['text']
        return ai_text
    
    def generate_insights(self, user, user_message, ai_response):
        """Generate AI insights based on the conversation"""
        insights = []
        
        # Simple insight generation based on keywords
        message_lower = user_message.lower()
        
        if 'budget' in message_lower and 'over' in message_lower:
            # Check for budget overruns
            over_budgets = Budget.objects.filter(
                user=user,
                is_active=True,
                spent_amount__gt=F('limit_amount')
            )
            if over_budgets.exists():
                insights.append(AIInsight(
                    user=user,
                    insight_type='BUDGET_ALERT',
                    title='Budget Overrun Detected',
                    description=f'You have {over_budgets.count()} budget(s) exceeding their limits.',
                    priority=8
                ))
        
        if 'subscription' in message_lower:
            # Detect potential subscriptions
            recurring_transactions = Transaction.objects.filter(
                account__user=user,
                is_recurring=True
            )
            if recurring_transactions.exists():
                insights.append(AIInsight(
                    user=user,
                    insight_type='SUBSCRIPTION_DETECTED',
                    title='Recurring Subscriptions Found',
                    description=f'You have {recurring_transactions.count()} recurring transactions.',
                    priority=5
                ))
        
        # Save insights
        for insight in insights:
            insight.save()
        
        return insights
    
    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')


class AIConversationListView(APIView):
    """List and create AI conversations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        conversations = AIConversation.objects.filter(user=request.user)
        serializer = AIConversationSerializer(conversations, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = AIConversationCreateSerializer(data=request.data)
        if serializer.is_valid():
            conversation = serializer.save(user=request.user)
            return Response(
                AIConversationSerializer(conversation).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIConversationDetailView(APIView):
    """Get, update, and delete AI conversations"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id, user=request.user)
            serializer = AIConversationSerializer(conversation)
            return Response(serializer.data)
        except AIConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, conversation_id):
        try:
            conversation = AIConversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AIConversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class AIInsightListView(APIView):
    """List and create AI insights"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        is_read = request.query_params.get('is_read')
        is_dismissed = request.query_params.get('is_dismissed')
        
        insights = AIInsight.objects.filter(user=request.user)
        
        if is_read is not None:
            insights = insights.filter(is_read=is_read.lower() == 'true')
        if is_dismissed is not None:
            insights = insights.filter(is_dismissed=is_dismissed.lower() == 'true')
        
        serializer = AIInsightSerializer(insights, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = AIInsightCreateSerializer(data=request.data)
        if serializer.is_valid():
            insight = serializer.save(user=request.user)
            return Response(
                AIInsightSerializer(insight).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AIInsightDetailView(APIView):
    """Get, update, and delete AI insights"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, insight_id):
        try:
            insight = AIInsight.objects.get(id=insight_id, user=request.user)
            serializer = AIInsightSerializer(insight)
            return Response(serializer.data)
        except AIInsight.DoesNotExist:
            return Response(
                {"error": "Insight not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def patch(self, request, insight_id):
        try:
            insight = AIInsight.objects.get(id=insight_id, user=request.user)
            serializer = AIInsightSerializer(insight, data=request.data, partial=True)
            
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except AIInsight.DoesNotExist:
            return Response(
                {"error": "Insight not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
    def delete(self, request, insight_id):
        try:
            insight = AIInsight.objects.get(id=insight_id, user=request.user)
            insight.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except AIInsight.DoesNotExist:
            return Response(
                {"error": "Insight not found"},
                status=status.HTTP_404_NOT_FOUND
            )


class AIUsageSummaryView(APIView):
    """Get AI usage statistics"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        start_date = timezone.now() - timedelta(days=days)
        
        logs = AIUsageLog.objects.filter(
            user=request.user,
            created_at__gte=start_date
        )
        
        total_requests = logs.count()
        total_tokens = logs.aggregate(total=Sum('tokens_used'))['total'] or 0
        avg_response_time = logs.aggregate(avg=Sum('response_time_ms') / Count('id'))['avg'] or 0
        success_rate = (logs.filter(success=True).count() / total_requests * 100) if total_requests > 0 else 0
        
        # Requests by endpoint
        requests_by_endpoint = {}
        for log in logs:
            endpoint = log.endpoint
            if endpoint not in requests_by_endpoint:
                requests_by_endpoint[endpoint] = 0
            requests_by_endpoint[endpoint] += 1
        
        # Daily usage
        daily_usage = []
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).date()
            daily_logs = logs.filter(created_at__date=date)
            daily_usage.append({
                'date': date.isoformat(),
                'requests': daily_logs.count(),
                'tokens': daily_logs.aggregate(total=Sum('tokens_used'))['total'] or 0
            })
        
        summary_data = {
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'avg_response_time': round(avg_response_time, 2),
            'success_rate': round(success_rate, 2),
            'requests_by_endpoint': requests_by_endpoint,
            'daily_usage': daily_usage
        }
        
        serializer = AIUsageSummarySerializer(summary_data)
        return Response(serializer.data)


class FinancialAnalysisView(APIView):
    """Generate AI-powered financial analysis"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = FinancialAnalysisSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        analysis_type = serializer.validated_data['analysis_type']
        period = serializer.validated_data.get('period', 'month')
        
        # Gather data based on analysis type
        context = self.gather_analysis_context(request.user, analysis_type, period)
        
        # Call AI for analysis
        analysis_prompt = self.build_analysis_prompt(analysis_type, context)
        
        try:
            ai_response = self.call_gemini_ai(analysis_prompt)
            
            # Log usage
            AIUsageLog.objects.create(
                user=request.user,
                endpoint=f'financial_analysis_{analysis_type}',
                tokens_used=len(analysis_prompt.split()) + len(ai_response.split()),
                response_time_ms=0,
                success=True
            )
            
            return Response({
                'analysis_type': analysis_type,
                'analysis': ai_response,
                'generated_at': timezone.now().isoformat()
            })
            
        except Exception as e:
            return Response(
                {"error": f"Analysis failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def gather_analysis_context(self, user, analysis_type, period):
        """Gather relevant data for analysis"""
        context = {}
        
        # Date range
        end_date = timezone.now()
        if period == 'month':
            start_date = end_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        elif period == 'year':
            start_date = end_date.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start_date = end_date - timedelta(days=30)
        
        context['period'] = period
        context['start_date'] = start_date.strftime('%Y-%m-%d')
        context['end_date'] = end_date.strftime('%Y-%m-%d')
        
        # Transactions
        transactions = Transaction.objects.filter(
            account__user=user,
            timestamp__gte=start_date,
            timestamp__lte=end_date
        )
        context['total_income'] = transactions.filter(type='INCOME').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        context['total_expenses'] = transactions.filter(type='EXPENSE').aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0.00')
        
        return context
    
    def build_analysis_prompt(self, analysis_type, context):
        """Build prompt for financial analysis"""
        prompts = {
            'SPENDING_SUMMARY': f"Analyze my spending patterns for {context['period']}. Total income: ${context['total_income']}, Total expenses: ${context['total_expenses']}. Provide insights on spending habits and recommendations.",
            'BUDGET_ANALYSIS': f"Analyze my budget performance. Period: {context['period']}. Provide recommendations for budget optimization.",
            'SAVINGS_RECOMMENDATIONS': f"Based on my financial data for {context['period']}, provide savings recommendations. Income: ${context['total_income']}, Expenses: ${context['total_expenses']}.",
        }
        return prompts.get(analysis_type, "Provide a comprehensive financial analysis.")
    
    def call_gemini_ai(self, prompt):
        """Call Gemini AI API"""
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,
            }
        }
        
        response = requests.post(api_url, json=payload, timeout=15)
        response.raise_for_status()
        response_json = response.json()
        
        return response_json['candidates'][0]['content']['parts'][0]['text']


class NaturalLanguageSearchView(APIView):
    """Natural language search for transactions"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = NaturalLanguageSearchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        query = serializer.validated_data['query']
        limit = serializer.validated_data.get('limit', 20)
        
        # Use AI to parse the query and extract search parameters
        search_params = self.parse_search_query(query)
        
        # Search transactions
        transactions = Transaction.objects.filter(account__user=request.user)
        
        if 'category' in search_params:
            transactions = transactions.filter(category__icontains=search_params['category'])
        if 'min_amount' in search_params:
            transactions = transactions.filter(amount__gte=search_params['min_amount'])
        if 'max_amount' in search_params:
            transactions = transactions.filter(amount__lte=search_params['max_amount'])
        if 'start_date' in search_params:
            transactions = transactions.filter(timestamp__gte=search_params['start_date'])
        if 'end_date' in search_params:
            transactions = transactions.filter(timestamp__lte=search_params['end_date'])
        
        transactions = transactions.order_by('-timestamp')[:limit]
        
        from apps.ledger.serializers import TransactionSerializer
        serializer = TransactionSerializer(transactions, many=True)
        
        return Response({
            'query': query,
            'parsed_filters': search_params,
            'results': serializer.data,
            'count': len(serializer.data)
        })
    
    def parse_search_query(self, query):
        """Use AI to parse natural language query into search parameters"""
        # Simple keyword-based parsing (in production, use AI)
        params = {}
        query_lower = query.lower()
        
        # Extract categories
        categories = ['food', 'restaurant', 'grocery', 'transport', 'gas', 'entertainment', 'shopping']
        for category in categories:
            if category in query_lower:
                params['category'] = category
                break
        
        # Extract time periods
        if 'last month' in query_lower:
            from datetime import datetime, timedelta
            end_date = timezone.now().replace(day=1) - timedelta(days=1)
            start_date = end_date.replace(day=1)
            params['start_date'] = start_date
            params['end_date'] = end_date
        elif 'this month' in query_lower:
            from datetime import datetime
            params['start_date'] = timezone.now().replace(day=1)
            params['end_date'] = timezone.now()
        
        return params