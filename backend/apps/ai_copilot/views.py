import uuid
import requests
import json
from django.conf import settings
from django.utils import timezone
from django.db.models import Sum, Count, F
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from datetime import datetime, timedelta, time
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
from apps.ledger.serializers import TransactionSerializer
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
            
            # Generate suggested follow-up questions
            suggested_questions = self.generate_suggested_questions(message_text, ai_response_text, financial_context)
            
            response_data = {
                'conversation_id': conversation.id,
                'message': AIMessageSerializer(user_message).data,
                'response': AIMessageSerializer(ai_message).data,
                'insights': AIInsightSerializer(insights, many=True).data if insights else [],
                'suggested_questions': suggested_questions
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
    
    def generate_suggested_questions(self, user_message, ai_response, financial_context):
        """Generate suggested follow-up questions based on conversation"""
        suggestions = []
        message_lower = user_message.lower()
        
        # Context-aware suggestions
        if 'budget' in message_lower:
            suggestions.extend([
                "How can I reduce my spending?",
                "Which budget category am I overspending in?",
                "Suggest ways to save money this month"
            ])
        elif 'save' in message_lower or 'saving' in message_lower:
            suggestions.extend([
                "What's my current savings rate?",
                "How much should I save for retirement?",
                "Show me my progress towards goals"
            ])
        elif 'invest' in message_lower:
            suggestions.extend([
                "How should I diversify my portfolio?",
                "What's my investment performance?",
                "Should I pay off debt or invest?"
            ])
        elif 'debt' in message_lower:
            suggestions.extend([
                "What's the best way to pay off my debt?",
                "Should I use the avalanche or snowball method?",
                "How much extra should I pay towards debt?"
            ])
        else:
            # Generic suggestions
            suggestions = [
                "Analyze my spending patterns",
                "How am I doing financially?",
                "What are my biggest expenses?"
            ]
        
        # Return top 3 suggestions
        return suggestions[:3]
    
    def generate_insights(self, user, user_message, ai_response):
        """Generate AI insights based on the conversation and user data"""
        insights = []
        
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
                description=f'You have {over_budgets.count()} budget(s) exceeding their limits. Review your spending to get back on track.',
                priority=8,
                action_url='/budgets'
            ))
        
        # Detect potential subscriptions
        recurring_transactions = Transaction.objects.filter(
            account__user=user,
            is_recurring=True
        )
        if recurring_transactions.exists():
            total_subscription_cost = sum(tx.amount for tx in recurring_transactions)
            insights.append(AIInsight(
                user=user,
                insight_type='SUBSCRIPTION_DETECTED',
                title='Recurring Subscriptions Found',
                description=f'You have {recurring_transactions.count()} recurring transactions totaling ${total_subscription_cost:.2f}/month. Review if all are needed.',
                priority=5,
                action_url='/transactions?filter=recurring'
            ))
        
        # Detect duplicate charges
        from datetime import timedelta
        recent_transactions = Transaction.objects.filter(
            account__user=user,
            timestamp__gte=timezone.now() - timedelta(days=30)
        )
        
        # Group by title and amount to find potential duplicates
        from django.db.models import Count
        duplicates = recent_transactions.values('title', 'amount').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicates.exists():
            insights.append(AIInsight(
                user=user,
                insight_type='DUPLICATE_CHARGE',
                title='Potential Duplicate Charges Detected',
                description=f'Found {duplicates.count()} potential duplicate transaction(s). Review your recent transactions.',
                priority=7,
                action_url='/transactions'
            ))
        
        # Calculate financial health score
        health_score = self.calculate_financial_health_score(user)
        if health_score < 60:
            insights.append(AIInsight(
                user=user,
                insight_type='FINANCIAL_HEALTH',
                title='Financial Health Score Below Average',
                description=f'Your financial health score is {health_score}/100. Focus on reducing debt and increasing savings.',
                priority=6,
                metadata={'score': health_score}
            ))
        
        # Check for upcoming bills
        upcoming_bills = Bill.objects.filter(
            user=user,
            is_active=True,
            is_paid=False,
            due_date__gte=timezone.now().date(),
            due_date__lte=timezone.now().date() + timedelta(days=7)
        )
        if upcoming_bills.exists():
            total_due = sum(bill.amount for bill in upcoming_bills)
            insights.append(AIInsight(
                user=user,
                insight_type='BILL_REMINDER',
                title='Upcoming Bills Due Soon',
                description=f'You have {upcoming_bills.count()} bill(s) due in the next 7 days totaling ${total_due:.2f}.',
                priority=9,
                action_url='/bills'
            ))
        
        # Savings opportunities
        if financial_context.get('total_income', 0) > 0:
            savings_rate = (financial_context.get('total_income', 0) - financial_context.get('total_expenses', 0)) / financial_context.get('total_income', 1)
            if savings_rate < 0.2:
                insights.append(AIInsight(
                    user=user,
                    insight_type='SAVINGS_OPPORTUNITY',
                    title='Low Savings Rate Detected',
                    description=f'Your current savings rate is {savings_rate*100:.1f}%. Financial experts recommend saving at least 20% of your income.',
                    priority=6,
                    action_url='/budgets'
                ))
        
        # Save insights
        for insight in insights:
            insight.save()
        
        return insights
    
    def calculate_financial_health_score(self, user):
        """Calculate overall financial health score (0-100)"""
        score = 50  # Base score
        
        # Factor 1: Savings rate (max +20)
        total_income = Transaction.objects.filter(
            account__user=user,
            type='INCOME',
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        total_expenses = Transaction.objects.filter(
            account__user=user,
            type='EXPENSE',
            timestamp__gte=timezone.now() - timedelta(days=30)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        if total_income > 0:
            savings_rate = (total_income - total_expenses) / total_income
            score += min(20, int(savings_rate * 100))
        
        # Factor 2: Budget adherence (max +15)
        budgets = Budget.objects.filter(user=user, is_active=True)
        if budgets.exists():
            on_track = sum(1 for b in budgets if b.percentage_used < 80)
            score += int((on_track / len(budgets)) * 15)
        
        # Factor 3: Debt management (max +15)
        debts = Debt.objects.filter(user=user, is_active=True)
        if not debts.exists():
            score += 15
        else:
            total_debt = sum(debt.total_balance for debt in debts)
            if total_debt < 5000:
                score += 10
            elif total_debt < 15000:
                score += 5
        
        # Penalty for high expenses relative to income
        if total_income > 0 and total_expenses > total_income:
            score -= 10
        
        return min(100, max(0, score))
    
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


class ReceiptUploadView(APIView):
    """Upload receipt and extract transaction data using OCR"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if 'receipt' not in request.FILES:
            return Response(
                {"error": "Receipt file is required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        receipt_file = request.FILES['receipt']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/jpg', 'application/pdf']
        if receipt_file.content_type not in allowed_types:
            return Response(
                {"error": "Invalid file type. Please upload JPEG, PNG, or PDF"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (max 10MB)
        if receipt_file.size > 10 * 1024 * 1024:
            return Response(
                {"error": "File size too large. Maximum size is 10MB"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Save receipt temporarily
            from django.core.files.storage import default_storage
            from django.core.files.base import ContentFile
            import os
            
            # Create unique filename
            ext = receipt_file.name.split('.')[-1]
            filename = f"receipts/{request.user.id}/{uuid.uuid4()}.{ext}"
            path = default_storage.save(filename, ContentFile(receipt_file.read()))
            
            # Extract text from receipt using OCR
            extracted_data = self.extract_receipt_data(path)
            
            # Create transaction from extracted data
            transaction = self.create_transaction_from_receipt(request.user, extracted_data)
            
            # Clean up temporary file
            default_storage.delete(path)
            
            return Response({
                'message': 'Receipt processed successfully',
                'extracted_data': extracted_data,
                'transaction': TransactionSerializer(transaction).data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Failed to process receipt: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def extract_receipt_data(self, file_path):
        """Extract data from receipt using OCR"""
        extracted_data = {
            'merchant': '',
            'amount': 0.0,
            'date': timezone.now().date().isoformat(),
            'items': [],
            'category': 'Other'
        }
        
        try:
            # Try to use Google Vision API if available
            if settings.GOOGLE_VISION_API_KEY:
                extracted_data = self.extract_with_google_vision(file_path)
            else:
                # Fallback to basic extraction
                extracted_data = self.extract_basic(file_path)
        except Exception as e:
            print(f"OCR extraction error: {e}")
        
        return extracted_data
    
    def extract_with_google_vision(self, file_path):
        """Extract text using Google Vision API"""
        import base64
        import json
        
        # Read file and encode to base64
        with open(file_path, 'rb') as image_file:
            image_content = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Prepare request
        api_url = f"https://vision.googleapis.com/v1/images:annotate?key={settings.GOOGLE_VISION_API_KEY}"
        
        payload = {
            "requests": [
                {
                    "image": {
                        "content": image_content
                    },
                    "features": [
                        {
                            "type": "TEXT_DETECTION",
                            "maxResults": 1
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        # Extract text
        if 'responses' in result and result['responses']:
            text_annotations = result['responses'][0].get('textAnnotations', [])
            if text_annotations:
                full_text = text_annotations[0].get('description', '')
                return self.parse_receipt_text(full_text)
        
        return self.extract_basic(file_path)
    
    def extract_basic(self, file_path):
        """Basic extraction without OCR API"""
        # In a real implementation, you might use Tesseract or another OCR library
        # For now, return placeholder data
        return {
            'merchant': 'Unknown Merchant',
            'amount': 0.0,
            'date': timezone.now().date().isoformat(),
            'items': [],
            'category': 'Other',
            'raw_text': ''
        }
    
    def parse_receipt_text(self, text):
        """Parse receipt text to extract merchant, amount, date"""
        import re
        from datetime import datetime
        
        extracted = {
            'merchant': 'Unknown Merchant',
            'amount': 0.0,
            'date': timezone.now().date().isoformat(),
            'items': [],
            'category': 'Other',
            'raw_text': text
        }
        
        # Extract amount (look for total, amount, etc.)
        amount_patterns = [
            r'total[:\s]*\$?(\d+\.?\d*)',
            r'amount[:\s]*\$?(\d+\.?\d*)',
            r'\$(\d+\.?\d*)\s*$',
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                extracted['amount'] = float(match.group(1))
                break
        
        # Extract date
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    date_str = match.group(1)
                    for fmt in ['%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y']:
                        try:
                            parsed_date = datetime.strptime(date_str, fmt).date()
                            extracted['date'] = parsed_date.isoformat()
                            break
                        except ValueError:
                            continue
                except Exception:
                    pass
                break
        
        # Extract merchant (usually first line or near store/shop keywords)
        lines = text.split('\n')
        for line in lines[:5]:  # Check first 5 lines
            if len(line.strip()) > 3 and not re.match(r'^\d+', line.strip()):
                extracted['merchant'] = line.strip()[:100]
                break
        
        # Use AI to categorize
        if extracted['amount'] > 0:
            extracted['category'] = self.categorize_with_ai(
                extracted['merchant'], 
                extracted['amount'], 
                text[:500]
            )
        
        return extracted
    
    def categorize_with_ai(self, merchant, amount, context=''):
        """Use AI to categorize the transaction"""
        from .services import GeminiCopilotService
        return GeminiCopilotService.categorize_transaction(merchant, amount, context)
    
    def create_transaction_from_receipt(self, user, extracted_data):
        """Create a transaction from extracted receipt data"""
        # Get user's default account or first active account
        account = Account.objects.filter(user=user, is_active=True).first()
        if not account:
            raise ValueError("No active account found. Please create an account first.")
        
        # Parse date
        try:
            parsed_date = datetime.strptime(extracted_data['date'], '%Y-%m-%d').date()
            timestamp = timezone.make_aware(datetime.combine(parsed_date, time.min))
        except Exception:
            timestamp = timezone.now()
        
        # Create transaction
        transaction = Transaction.objects.create(
            account=account,
            title=f"Receipt: {extracted_data['merchant']}",
            amount=Decimal(str(extracted_data['amount'])),
            category=extracted_data['category'],
            type='EXPENSE',
            timestamp=timestamp,
            note=f"Auto-categorized from receipt. Items: {', '.join(extracted_data.get('items', [])[:3])}",
            tags="Receipt, Auto-Categorized"
        )
        
        return transaction


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
        # Use AI for better parsing
        try:
            search_params = self.parse_with_ai(query)
            if search_params:
                return search_params
        except Exception:
            pass
        
        # Fallback to keyword-based parsing
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
    
    def parse_with_ai(self, query):
        """Use Gemini AI to parse natural language query"""
        prompt = f"""Parse this financial search query into structured parameters. Return JSON only.
        
Query: "{query}"

Extract these parameters if present:
- category (e.g., food, transport, shopping)
- min_amount (number)
- max_amount (number)
- start_date (YYYY-MM-DD format)
- end_date (YYYY-MM-DD format)
- merchant (store/merchant name)
- type (INCOME or EXPENSE)

Return format: {{"category": "...", "min_amount": 0, "max_amount": 0, "start_date": "...", "end_date": "...", "merchant": "...", "type": "..."}}

Only include parameters that are clearly mentioned in the query. Return empty JSON {{}} if none found."""

        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 200,
            }
        }
        
        response = requests.post(api_url, json=payload, timeout=10)
        response.raise_for_status()
        result = response.json()
        
        ai_text = result['candidates'][0]['content']['parts'][0]['text']
        
        # Extract JSON from response
        import json
        import re
        json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
        if json_match:
            params = json.loads(json_match.group())
            # Clean up empty values
            return {k: v for k, v in params.items() if v not in [None, '', 0]}
        
        return {}
