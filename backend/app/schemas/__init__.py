"""
Pydantic Schemas Package.

Defines request/response models, validation rules, and serialization
for all API endpoints. Uses Pydantic v2 for performance and type safety.

Schemas:
    - auth: Authentication request/response models
    - customer: Customer CRUD models
    - loan: Loan application and decision models
    - churn: Churn prediction and segmentation models
    - credit: Credit scoring and risk assessment models
    - statement: Statement upload and processing models

Future Enhancements:
    - Add field-level encryption for PII
    - Add custom validators for Kenyan-specific formats (phone, ID)
    - Add schema versioning for API evolution
"""