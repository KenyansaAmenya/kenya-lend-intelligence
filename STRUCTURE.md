``
kenya-lend-intelligence/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── dependencies.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── customer.py
│   │   │   ├── loan.py
│   │   │   ├── activity.py
│   │   │   ├── transaction.py
│   │   │   ├── prediction.py
│   │   │   ├── segment.py
│   │   │   └── retention.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── customer.py
│   │   │   ├── loan.py
│   │   │   ├── churn.py
│   │   │   ├── credit.py
│   │   │   └── statement.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── customers.py
│   │   │   ├── loans.py
│   │   │   ├── churn.py
│   │   │   ├── credit.py
│   │   │   ├── statements.py
│   │   │   ├── datasets.py
│   │   │   └── retention.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py
│   │   │   ├── customer_service.py
│   │   │   ├── loan_service.py
│   │   │   ├── churn_service.py
│   │   │   ├── credit_service.py
│   │   │   ├── statement_service.py
│   │   │   ├── feature_engineering.py
│   │   │   ├── segmentation_service.py
│   │   │   ├── retention_service.py
│   │   │   └── ml/
│   │   │       ├── __init__.py
│   │   │       ├── base_model.py
│   │   │       ├── credit_model.py
│   │   │       ├── default_model.py
│   │   │       ├── churn_model.py
│   │   │       ├── model_trainer.py
│   │   │       ├── model_registry.py
│   │   │       └── explainability.py
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base_repository.py
│   │   │   ├── user_repository.py
│   │   │   ├── customer_repository.py
│   │   │   ├── loan_repository.py
│   │   │   ├── activity_repository.py
│   │   │   ├── transaction_repository.py
│   │   │   └── prediction_repository.py
│   │   ├── connectors/
│   │   │   ├── __init__.py
│   │   │   ├── base_connector.py
│   │   │   ├── kaggle_connector.py
│   │   │   ├── world_bank_connector.py
│   │   │   ├── macroeconomic_connector.py
│   │   │   ├── government_data_connector.py
│   │   │   └── external_dataset_connector.py
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── security.py
│   │   │   ├── logging_config.py
│   │   │   ├── exceptions.py
│   │   │   └── audit.py
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── file_utils.py
│   │       ├── date_utils.py
│   │       └── validators.py
│   ├── ml/
│   │   ├── __init__.py
│   │   ├── training/
│   │   │   ├── __init__.py
│   │   │   └── train_models.py
│   │   └── inference/
│   │       ├── __init__.py
│   │       └── predict.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_auth.py
│   │   ├── test_customers.py
│   │   ├── test_loans.py
│   │   └── test_churn.py
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env
│   ├── alembic.ini
│   └── pyproject.toml
├── .github/
│   └── workflows/
│       └── ci-cd.yml
├── render.yaml
├── README.md
├── ARCHITECTURE.md
├── API_DOCUMENTATION.md
├── DEPLOYMENT.md
└── DATA_DICTIONARY.md

``