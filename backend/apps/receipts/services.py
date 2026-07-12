import base64
import os
import re
from datetime import datetime
from decimal import Decimal

import requests
from django.conf import settings
from django.utils import timezone

from apps.ai_copilot.services import GeminiCopilotService


class ReceiptProcessingService:
    """Extract structured data from uploaded receipt files."""

    @staticmethod
    def process(file_path):
        """Return a normalized receipt payload from OCR or fallback parsing."""
        if settings.GOOGLE_VISION_API_KEY:
            try:
                return ReceiptProcessingService._process_with_google_vision(file_path)
            except Exception:
                pass

        return ReceiptProcessingService._process_basic(file_path)

    @staticmethod
    def _process_with_google_vision(file_path):
        with open(file_path, 'rb') as receipt_file:
            image_content = base64.b64encode(receipt_file.read()).decode('utf-8')

        api_url = (
            'https://vision.googleapis.com/v1/images:annotate?'
            f'key={settings.GOOGLE_VISION_API_KEY}'
        )
        payload = {
            'requests': [
                {
                    'image': {'content': image_content},
                    'features': [{'type': 'TEXT_DETECTION', 'maxResults': 1}],
                }
            ]
        }

        response = requests.post(api_url, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        text_annotations = result.get('responses', [{}])[0].get('textAnnotations', [])
        if text_annotations:
            return ReceiptProcessingService.parse_text(text_annotations[0].get('description', ''))

        return ReceiptProcessingService._process_basic(file_path)

    @staticmethod
    def _process_basic(file_path):
        raw_text = ''
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'rb') as receipt_file:
                    raw_text = receipt_file.read().decode('utf-8', errors='ignore')
            except Exception:
                raw_text = ''

        return ReceiptProcessingService.parse_text(raw_text)

    @staticmethod
    def parse_text(text):
        """Parse text into merchant, amount, date, and category fields."""
        extracted = {
            'merchant': 'Unknown Merchant',
            'amount': Decimal('0.00'),
            'date': timezone.now().date().isoformat(),
            'items': [],
            'category': 'Other',
            'raw_text': text,
        }

        amount_patterns = [
            r'total[:\s]*\$?(\d+\.\d{2})',
            r'amount[:\s]*\$?(\d+\.\d{2})',
            r'\$(\d+\.\d{2})\s*$',
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                extracted['amount'] = Decimal(match.group(1))
                break

        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                date_text = match.group(1)
                for fmt in ('%m/%d/%Y', '%m-%d-%Y', '%Y-%m-%d', '%d/%m/%Y'):
                    try:
                        extracted['date'] = datetime.strptime(date_text, fmt).date().isoformat()
                        break
                    except ValueError:
                        continue
                break

        for line in text.split('\n')[:5]:
            line = line.strip()
            if len(line) > 3 and not re.match(r'^\d+', line):
                extracted['merchant'] = line[:100]
                break

        if extracted['amount'] > 0:
            extracted['category'] = GeminiCopilotService.categorize_transaction(
                extracted['merchant'],
                extracted['amount'],
                text[:500],
            )

        return extracted