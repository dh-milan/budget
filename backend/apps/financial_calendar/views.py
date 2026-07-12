from datetime import datetime, timedelta

from django.utils import timezone
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import FinancialCalendarEvent
from .serializers import FinancialCalendarEventSerializer


class FinancialCalendarEventViewSet(viewsets.ModelViewSet):
    """Manage financial calendar events."""

    serializer_class = FinancialCalendarEventSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = FinancialCalendarEvent.objects.filter(user=self.request.user)

        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)

        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(event_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(event_date__lte=end_date)

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        """Return events grouped by date for the calendar view."""
        today = timezone.now().date()
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date:
            start_date = datetime.fromisoformat(start_date).date()
        else:
            start_date = today.replace(day=1)

        if end_date:
            end_date = datetime.fromisoformat(end_date).date()
        else:
            end_date = (start_date + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        events = self.get_queryset().filter(event_date__gte=start_date, event_date__lte=end_date)
        serialized = FinancialCalendarEventSerializer(events, many=True, context={'request': request})

        grouped = {}
        for item in serialized.data:
            grouped.setdefault(item['event_date'], []).append(item)

        return Response(
            {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'total_events': events.count(),
                'calendar': [
                    {'date': date_key, 'events': grouped[date_key]}
                    for date_key in sorted(grouped.keys())
                ],
            }
        )

    @action(detail=False, methods=['get'])
    def reminders(self, request):
        """Return upcoming reminder events."""
        days = int(request.query_params.get('days', 30))
        today = timezone.now().date()
        until = today + timedelta(days=days)

        events = self.get_queryset().filter(
            is_reminder_enabled=True,
            event_date__gte=today,
            event_date__lte=until,
        )
        serializer = FinancialCalendarEventSerializer(events, many=True, context={'request': request})

        return Response(
            {
                'days': days,
                'count': events.count(),
                'results': serializer.data,
            }
        )