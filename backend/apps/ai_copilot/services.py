import json

import requests
from django.conf import settings


class GeminiCopilotService:
    """Utility methods for Gemini-backed AI helpers."""

    @staticmethod
    def categorize_transaction(title, amount, note=''):
        """Return a likely transaction category for the given transaction."""
        if not settings.GEMINI_API_KEY:
            return GeminiCopilotService._fallback_category(title, note)

        prompt = (
            "Classify this financial transaction into a short category label. "
            "Return only the category name.\n\n"
            f"Title: {title}\n"
            f"Amount: {amount}\n"
            f"Note: {note or ''}"
        )

        api_url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-1.5-flash:generateContent?key={settings.GEMINI_API_KEY}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 20,
            },
        }

        try:
            response = requests.post(api_url, json=payload, timeout=15)
            response.raise_for_status()
            response_json = response.json()
            category = response_json['candidates'][0]['content']['parts'][0]['text'].strip()
            return category or GeminiCopilotService._fallback_category(title, note)
        except (requests.RequestException, KeyError, IndexError, ValueError, json.JSONDecodeError):
            return GeminiCopilotService._fallback_category(title, note)

    @staticmethod
    def _fallback_category(title, note=''):
        """Simple local fallback when the Gemini API is unavailable."""
        text = f"{title} {note}".lower()

        keyword_map = {
            'grocer': 'Groceries',
            'supermarket': 'Groceries',
            'restaurant': 'Dining',
            'coffee': 'Dining',
            'fuel': 'Transportation',
            'gas': 'Transportation',
            'uber': 'Transportation',
            'lyft': 'Transportation',
            'rent': 'Housing',
            'mortgage': 'Housing',
            'salary': 'Income',
            'payroll': 'Income',
            'subscription': 'Subscriptions',
            'netflix': 'Subscriptions',
            'utility': 'Utilities',
            'electric': 'Utilities',
            'water': 'Utilities',
            'phone': 'Utilities',
        }

        for keyword, category in keyword_map.items():
            if keyword in text:
                return category

        return 'Other'