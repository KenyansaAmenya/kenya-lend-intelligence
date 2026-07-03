# Audit Logging Module.
# this will Record all significant business events for compliance,
# security monitoring, and forensic analysis.

import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from app.core.logging_config import get_logger

logger = get_logger(__name__)


class AuditEventType(str, Enum):
    # Authentication events
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    LOGIN_FAILED = "LOGIN_FAILED"
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    
    # Customer events
    CUSTOMER_CREATED = "CUSTOMER_CREATED"
    CUSTOMER_UPDATED = "CUSTOMER_UPDATED"
    CUSTOMER_DELETED = "CUSTOMER_DELETED"
    CUSTOMER_VIEWED = "CUSTOMER_VIEWED"
    
    # Loan events
    LOAN_APPLICATION_SUBMITTED = "LOAN_APPLICATION_SUBMITTED"
    LOAN_APPROVED = "LOAN_APPROVED"
    LOAN_REJECTED = "LOAN_REJECTED"
    LOAN_DISBURSED = "LOAN_DISBURSED"
    LOAN_REPAID = "LOAN_REPAID"
    LOAN_DEFAULTED = "LOAN_DEFAULTED"
    
    # Prediction events
    CREDIT_SCORE_GENERATED = "CREDIT_SCORE_GENERATED"
    DEFAULT_PREDICTION_MADE = "DEFAULT_PREDICTION_MADE"
    CHURN_PREDICTION_MADE = "CHURN_PREDICTION_MADE"
    
    # Data access events
    STATEMENT_UPLOADED = "STATEMENT_UPLOADED"
    DATA_EXPORTED = "DATA_EXPORTED"
    REPORT_GENERATED = "REPORT_GENERATED"
    
    # Admin events
    USER_CREATED = "USER_CREATED"
    USER_ROLE_CHANGED = "USER_ROLE_CHANGED"
    MODEL_RETRAINED = "MODEL_RETRAINED"
    CONFIGURATION_CHANGED = "CONFIGURATION_CHANGED"


class AuditLogger:
    
    @staticmethod
    async def log_event(
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:

        audit_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "user_id": user_id,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "ip_address": ip_address,
            "user_agent": user_agent,
            "service": "kenya-lend-intelligence",
            "version": "0.1.0",
        }
        
        # TODO: Store in immutable audit log table in PostgreSQL
        # TODO: Forward to SIEM system (Splunk, ELK, Datadog)
        # TODO: Add real-time alerting for high-risk events
        
        logger.info(
            "audit_event",
            **audit_entry,
        )
    
    @staticmethod
    async def log_prediction(
        model_name: str,
        prediction_type: str,
        customer_id: str,
        prediction_value: Any,
        confidence: Optional[float] = None,
        features_used: Optional[list[str]] = None,
        shap_values: Optional[dict[str, float]] = None,
    ) -> None:

        await AuditLogger.log_event(
            event_type=AuditEventType.CREDIT_SCORE_GENERATED
            if prediction_type == "credit"
            else AuditEventType.DEFAULT_PREDICTION_MADE
            if prediction_type == "default"
            else AuditEventType.CHURN_PREDICTION_MADE,
            resource_type="prediction",
            resource_id=customer_id,
            details={
                "model_name": model_name,
                "prediction_type": prediction_type,
                "prediction_value": prediction_value,
                "confidence": confidence,
                "features_used": features_used,
                "shap_values": shap_values,
            },
        )


# TODO: Add audit log retention policy management
# TODO: Add audit log integrity verification (checksums)
# TODO: Add tamper-evident audit logging
# TODO: Add audit log export for regulatory reporting


# Future Enhancements:
    # - Add immutable audit log storage (WORM)
    # - Add real-time audit alerting
    # - Add audit log encryption
    # - Add blockchain-based audit trails for regulatory compliance
