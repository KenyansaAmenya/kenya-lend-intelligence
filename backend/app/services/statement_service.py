# Statement Processing Service.
# Handles M-Pesa and bank statement uploads, parsing, and analysis.
# Extracts financial features for credit scoring and risk assessment.

import csv
import io
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from uuid import UUID

import pandas as pd
from fastapi import UploadFile

from app.config import settings
from app.core.audit import AuditEventType, AuditLogger
from app.core.exceptions import ValidationError
from app.core.logging_config import get_logger
from app.schemas.statement import StatementAnalysisResponse, StatementUploadResponse

logger = get_logger(__name__)

class StatementService:
    
    def __init__(self):
        self.audit = AuditLogger()
    
    async def process_upload(self, file: UploadFile, customer_id: UUID, statement_type: str) -> StatementUploadResponse:
        # Validate file type
        allowed_types = [
            "text/csv",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/pdf",
        ]
        
        if file.content_type not in allowed_types:
            raise ValidationError(f"Unsupported file type: {file.content_type}")
        
        # Read file content
        content = await file.read()
        file_size = len(content)
        
        # TODO: Upload to Supabase Storage
        # For MVP, we'll process in memory
        
        logger.info(
            "statement_uploaded",
            customer_id=str(customer_id),
            statement_type=statement_type,
            filename=file.filename,
            size=file_size,
        )
        
        await self.audit.log_event(
            event_type=AuditEventType.STATEMENT_UPLOADED,
            resource_type="customer",
            resource_id=str(customer_id),
            details={
                "statement_type": statement_type,
                "filename": file.filename,
                "size": file_size,
            },
        )
        
        return StatementUploadResponse(
            upload_id=UUID(int=0),  # TODO: Generate proper UUID
            customer_id=customer_id,
            statement_type=statement_type,
            file_name=file.filename or "unknown",
            file_size=file_size,
            status="PENDING",
            storage_path=f"raw/{statement_type}/{customer_id}/{file.filename}",
            uploaded_at=datetime.now(timezone.utc),
        )
    
    async def parse_csv_statement(self, content: bytes, statement_type: str) -> List[Dict]:
        try:
            df = pd.read_csv(io.BytesIO(content))
            
            if statement_type == "mpesa":
                return self._parse_mpesa_csv(df)
            else:
                return self._parse_bank_csv(df)
        except Exception as e:
            logger.error("csv_parse_error", error=str(e))
            raise ValidationError(f"Failed to parse CSV: {str(e)}")
    
    def _parse_mpesa_csv(self, df: pd.DataFrame) -> List[Dict]:
        transactions = []
        
        for _, row in df.iterrows():
            try:
                # Determine amount and type
                withdrawn = self._parse_amount(row.get("Withdrawn", 0))
                paid_in = self._parse_amount(row.get("Paid In", 0))
                
                if paid_in > 0:
                    amount = paid_in
                    tx_type = "RECEIVE"
                else:
                    amount = -withdrawn
                    tx_type = self._classify_mpesa_transaction(row.get("Details", ""))
                
                transactions.append({
                    "transaction_date": pd.to_datetime(row.get("Date")),
                    "amount": amount,
                    "transaction_type": tx_type,
                    "description": str(row.get("Details", "")),
                    "balance": self._parse_amount(row.get("Balance", 0)),
                })
            except Exception as e:
                logger.warning("mpesa_row_parse_error", error=str(e))
                continue
        
        return transactions
    
    def _parse_bank_csv(self, df: pd.DataFrame) -> List[Dict]:
        transactions = []
        
        for _, row in df.iterrows():
            try:
                debit = self._parse_amount(row.get("Debit", 0))
                credit = self._parse_amount(row.get("Credit", 0))
                
                if credit > 0:
                    amount = credit
                    tx_type = "CREDIT"
                else:
                    amount = -debit
                    tx_type = "DEBIT"
                
                transactions.append({
                    "transaction_date": pd.to_datetime(row.get("Date")),
                    "amount": amount,
                    "transaction_type": tx_type,
                    "description": str(row.get("Description", "")),
                    "balance": self._parse_amount(row.get("Balance", 0)),
                })
            except Exception as e:
                logger.warning("bank_row_parse_error", error=str(e))
                continue
        
        return transactions
    
    def _parse_amount(self, value) -> float:
        if pd.isna(value):
            return 0.0
        if isinstance(value, (int, float)):
            return float(value)
        # Remove commas and currency symbols
        cleaned = str(value).replace(",", "").replace("KES", "").replace("Ksh", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return 0.0
    
    def _classify_mpesa_transaction(self, details: str) -> str:
        details_upper = details.upper()
        
        if "SEND" in details_upper or "TO" in details_upper:
            return "SEND_MONEY"
        elif "PAYBILL" in details_upper or "BILL" in details_upper:
            return "PAYBILL"
        elif "BUY GOODS" in details_upper or "TILL" in details_upper:
            return "BUY_GOODS"
        elif "WITHDRAW" in details_upper or "ATM" in details_upper:
            return "WITHDRAWAL"
        elif "AIRTIME" in details_upper or "TOP UP" in details_upper:
            return "AIRTIME"
        elif "RECEIVED" in details_upper:
            return "RECEIVE"
        else:
            return "OTHER"
    
    async def analyze_statement(self, customer_id: UUID, statement_type: str) -> StatementAnalysisResponse:
        
        return StatementAnalysisResponse(
            customer_id=customer_id,
            statement_type=statement_type,
            analysis_date=datetime.now(timezone.utc),
            period_covered={"start": "2024-01-01", "end": "2024-03-31"},
            total_income=135000.0,
            average_monthly_income=45000.0,
            income_sources=[
                {"source": "Salary", "amount": 120000.0, "frequency": "monthly"},
                {"source": "Side Business", "amount": 15000.0, "frequency": "irregular"},
            ],
            income_stability_score=85.0,
            salary_detected=True,
            total_expenses=95000.0,
            average_monthly_expenses=31667.0,
            expense_categories=[
                {"category": "Utilities", "amount": 15000.0},
                {"category": "Food", "amount": 25000.0},
                {"category": "Transport", "amount": 20000.0},
                {"category": "Rent", "amount": 30000.0},
                {"category": "Other", "amount": 5000.0},
            ],
            spending_stability_score=75.0,
            total_savings=40000.0,
            savings_rate=0.296,
            savings_trend="STABLE",
            net_cash_flow=40000.0,
            cash_flow_trend="POSITIVE",
            negative_balance_days=0,
            gambling_indicators=None,
            frequent_overdrafts=False,
            irregular_income_pattern=False,
            financial_health_score=78.0,
        )
    
    # TODO: Add PDF parsing with OCR
    # TODO: Add Excel parsing
    # TODO: Add statement fraud detection
    # TODO: Add real-time transaction streaming