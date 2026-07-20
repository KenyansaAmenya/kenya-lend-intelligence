# KenyaLend Intelligence

KenyaLend Intelligence is a backend platform for Kenyan digital lenders that combines customer intelligence, churn prediction, credit scoring, statement processing, and loan decisioning in a single FastAPI service. The project is designed as an API-first foundation for lenders that want to combine internal loan and customer data with M-Pesa statements, bank statements, and external macroeconomic datasets.

> **Project status:** Alpha (`0.1.0`). Several endpoints and integrations are scaffolded and documented for extension, while some workflows still use placeholder logic or TODO-backed implementations.

## Table of Contents

- [What This Project Does](#what-this-project-does)
- [Core Capabilities](#core-capabilities)
- [Architecture at a Glance](#architecture-at-a-glance)
- [Technology Stack](#technology-stack)
- [Repository Layout](#repository-layout)
- [Domain Model](#domain-model)
- [API Surface](#api-surface)
- [Machine Learning Components](#machine-learning-components)
- [External Data and Integrations](#external-data-and-integrations)
- [Configuration](#configuration)
- [Prerequisites](#prerequisites)
- [Quick Start: Local Python Environment](#quick-start-local-python-environment)
- [Quick Start: Docker Compose](#quick-start-docker-compose)
- [Database Migrations](#database-migrations)
- [Authentication and Authorization](#authentication-and-authorization)
- [Running Tests and Quality Checks](#running-tests-and-quality-checks)
- [Deployment](#deployment)
- [Operational Notes](#operational-notes)
- [Development Workflow](#development-workflow)
- [Security and Compliance Considerations](#security-and-compliance-considerations)
- [Roadmap](#roadmap)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## What This Project Does

KenyaLend Intelligence helps digital lending teams make more informed customer and loan decisions by providing APIs for:

1. **Customer management** - Create, search, update, and inspect borrower profiles.
2. **Loan lifecycle operations** - Submit applications, approve or reject loans, and summarize portfolio state.
3. **Credit decisioning** - Generate credit scores, risk levels, affordability estimates, default probabilities, and loan recommendations.
4. **Churn prediction** - Identify customers at risk of inactivity or attrition and segment customer cohorts.
5. **Retention actions** - Generate recommendations and track intervention actions for at-risk customers.
6. **Statement ingestion** - Upload M-Pesa and bank statements for downstream analysis.
7. **Dataset ingestion** - Upload or fetch external datasets for data science workflows.
8. **ML model operations** - Train, register, load, and explain models for credit, default, and churn workflows.

The system is organized as a modular FastAPI application with explicit separation between API routers, service-layer business logic, repositories, SQLAlchemy models, Pydantic schemas, ML services, and external data connectors.

## Core Capabilities

### Customer Intelligence

- Customer CRUD-style API endpoints.
- Search and filtering by query, location, and employment status.
- Customer health scoring through service-layer feature aggregation.
- Structured customer, activity, loan, transaction, prediction, and segment models.

### Credit Scoring and Risk Assessment

- Credit score generation for a customer.
- Probability-of-default estimation.
- Risk-level classification.
- Recommended credit limits, loan amounts, and interest rates.
- Score trends and distribution endpoints for analytics dashboards.

### Loan Decisioning

- Loan application endpoint.
- Manual loan approval and rejection endpoints.
- Automated decision endpoints for M-Pesa, bank, or combined statement inputs.
- Portfolio summary endpoint.
- Decision explanations containing credit score factors and risk assessment context.

### Churn Prediction and Retention

- Single-customer and batch churn prediction endpoints.
- At-risk customer discovery with configurable thresholds.
- Customer segmentation and segment distribution support.
- Retention recommendation generation for at-risk borrowers.
- Retention action creation and retrieval scaffolding.

### Statement and Dataset Processing

- M-Pesa statement upload endpoint.
- Bank statement upload endpoint.
- Statement analysis endpoint.
- External dataset upload and fetch scaffolding.
- Supabase storage bucket configuration for raw statements, processed data, model artifacts, and ML artifacts.

## Architecture at a Glance

```text
Client / Dashboard / Partner System
              |
              v
        FastAPI Application
              |
      +-------+--------+------------------+
      |                |                  |
 API Routers       Services          Dependencies
      |                |                  |
      v                v                  v
 Pydantic        Business Logic      Auth / DB Session
 Schemas              |
                      v
              Repositories / Models
                      |
                      v
          PostgreSQL / Supabase Storage
                      |
                      v
        ML Models, External Connectors,
        Statement Processing Pipelines
```

The application entry point is `backend/app/main.py`. It creates the FastAPI application, configures CORS and trusted host middleware, registers exception handlers, mounts all `/api/v1` routers, and exposes `/health` plus `/` utility endpoints.

## Technology Stack

| Layer | Tools |
| --- | --- |
| API framework | FastAPI, Uvicorn |
| Validation and settings | Pydantic v2, pydantic-settings, python-dotenv |
| Database | PostgreSQL, SQLAlchemy 2, asyncpg, psycopg2-binary |
| Migrations | Alembic |
| Authentication | JWT via python-jose, password hashing via passlib/bcrypt |
| Storage and backend services | Supabase client and configurable storage buckets |
| Data processing | pandas, NumPy, Polars, OpenPyXL, PyPDF2 |
| Machine learning | scikit-learn, XGBoost, LightGBM, CatBoost, SHAP, Optuna, imbalanced-learn |
| Observability | structlog, prometheus-client |
| Testing and quality | pytest, pytest-asyncio, pytest-cov, Black, isort, flake8, mypy |
| Containers | Docker, Docker Compose |
| Deployment | Render blueprint via `render.yaml` |

## Repository Layout

```text
kenya-lend-intelligence/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI routers grouped by business domain
│   │   ├── connectors/       # External data source connectors
│   │   ├── core/             # Security, exceptions, audit, logging
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── repositories/     # Database access abstractions
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic and ML service orchestration
│   │   ├── utils/            # Date, file, and validation helpers
│   │   ├── config.py         # Environment-backed application settings
│   │   ├── database.py       # SQLAlchemy engine/session configuration
│   │   ├── dependencies.py   # FastAPI dependency providers
│   │   └── main.py           # FastAPI application factory and router mounting
│   ├── alembic/              # Migration environment and revisions
│   ├── ml/                   # Training and inference entry points
│   ├── tests/                # pytest test suite
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   ├── pyproject.toml
│   └── .env.example
├── API_DOCUMENTATION.md
├── ARCHITECTURE.md
├── DATA_DICTIONARY.md
├── DEPLOYMENT.md
├── STRUCTURE.txt
├── render.yaml
└── README.md
```

## Domain Model

The initial database migration creates the core tables below:

| Table | Purpose |
| --- | --- |
| `users` | Application users, roles, activation status, password hashes, and timestamps. |
| `customers` | Borrower identity, phone, national ID, location, occupation, employment status, and income attributes. |
| `loans` | Loan applications, amounts, interest rates, status, approval/disbursement dates, balances, delinquency, and scores at application time. |
| `customer_activity` | App activity signals such as session duration, app opens, feature usage, device type, notifications, and engagement score. |
| `mpesa_transactions` | Parsed M-Pesa transaction records linked to customers. |
| `bank_transactions` | Parsed bank transaction records linked to customers. |
| `churn_predictions` | Churn probability, risk level, prediction date, model version, feature snapshot, and SHAP values. |
| `customer_segments` | Customer segment assignments for analytics and retention workflows. |
| `retention_actions` | Retention intervention actions, status, description, execution timestamps, and outcome. |

## API Surface

All versioned business endpoints are mounted below `/api/v1`. In development mode, interactive documentation is available at:

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`
- OpenAPI JSON: `http://localhost:8000/api/openapi.json`

Utility endpoints:

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/` | Basic application metadata. |
| `GET` | `/health` | Health check with version and environment. |

### Authentication: `/api/v1/auth/auth`

> The router currently defines its own `/auth` prefix and is also mounted under `/api/v1/auth`, so generated paths include `/api/v1/auth/auth/...`.

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/auth/auth/register` | Register a new user. |
| `POST` | `/api/v1/auth/auth/login` | Authenticate using OAuth2 password form fields and return access/refresh tokens. |
| `POST` | `/api/v1/auth/auth/refresh` | Refresh an access token. |
| `GET` | `/api/v1/auth/auth/me` | Return the current active user. |
| `POST` | `/api/v1/auth/auth/logout` | Logout placeholder; token blacklist support is planned. |

### Customers: `/api/v1/customers/customers`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/customers/customers` | Create a customer. |
| `GET` | `/api/v1/customers/customers` | List/search customers with optional filters. |
| `GET` | `/api/v1/customers/customers/{customer_id}` | Get detailed customer data. |
| `PUT` | `/api/v1/customers/customers/{customer_id}` | Update a customer. |
| `GET` | `/api/v1/customers/customers/{customer_id}/health` | Calculate customer health score. |

### Loans: `/api/v1/loans/loans`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/loans/loans/apply` | Submit a loan application. |
| `GET` | `/api/v1/loans/loans` | List loans. Filtering is scaffolded. |
| `GET` | `/api/v1/loans/loans/{loan_id}` | Retrieve a loan. |
| `POST` | `/api/v1/loans/loans/{loan_id}/approve` | Approve a loan. |
| `POST` | `/api/v1/loans/loans/{loan_id}/reject` | Reject a loan. |
| `POST` | `/api/v1/loans/loans/decision/mpesa` | Make a loan decision using M-Pesa-oriented analysis. |
| `POST` | `/api/v1/loans/loans/decision/bank` | Make a loan decision using bank-statement-oriented analysis. |
| `POST` | `/api/v1/loans/loans/decision/combined` | Make a loan decision using combined analysis. |
| `GET` | `/api/v1/loans/loans/portfolio/summary` | Get portfolio-level summary metrics. |

### Credit: `/api/v1/credit/credit`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/credit/credit/score` | Generate a credit score. |
| `POST` | `/api/v1/credit/credit/assess` | Assess credit risk and affordability. |
| `GET` | `/api/v1/credit/credit/score/{customer_id}` | Generate/retrieve credit score for a customer. |
| `GET` | `/api/v1/credit/credit/trends` | Return score trend data. |
| `GET` | `/api/v1/credit/credit/distribution` | Return credit score distribution buckets. |

### Churn: `/api/v1/churn/churn`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/churn/churn/predict` | Predict churn for one customer. |
| `POST` | `/api/v1/churn/churn/predict/batch` | Predict churn for a batch of customers. |
| `GET` | `/api/v1/churn/churn/{customer_id}` | Get churn prediction for one customer. |
| `GET` | `/api/v1/churn/churn/customers/at-risk` | List customers above a churn-risk threshold. |
| `GET` | `/api/v1/churn/churn/segments` | Return customer segments. |
| `GET` | `/api/v1/churn/churn/segments/distribution` | Return segment distribution. |
| `GET` | `/api/v1/churn/churn/trends` | Return churn trend data. |

### Statements: `/api/v1/statements/statements`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/statements/statements/mpesa/upload` | Upload an M-Pesa statement for a customer. |
| `POST` | `/api/v1/statements/statements/bank/upload` | Upload a bank statement for a customer. |
| `POST` | `/api/v1/statements/statements/analyze` | Analyze a previously uploaded statement. |

### Datasets: `/api/v1/datasets/datasets`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/datasets/datasets/external/upload` | Upload an external dataset. |
| `GET` | `/api/v1/datasets/datasets` | List external datasets. |
| `POST` | `/api/v1/datasets/datasets/external/fetch` | Fetch an external dataset from a source. |

### Retention: `/api/v1/retention/retention`

| Method | Path | Description |
| --- | --- | --- |
| `POST` | `/api/v1/retention/retention/recommendations` | Generate recommendations for at-risk customers. |
| `POST` | `/api/v1/retention/retention/actions` | Create a retention action. |
| `GET` | `/api/v1/retention/retention/actions/{customer_id}` | List retention actions for a customer. |

## Machine Learning Components

The project includes ML-oriented services and scripts for model training, inference, registry management, and explainability.

Important locations:

- `backend/app/services/ml/base_model.py` - shared model abstractions.
- `backend/app/services/ml/credit_model.py` - credit scoring model logic.
- `backend/app/services/ml/default_model.py` - default prediction model logic.
- `backend/app/services/ml/churn_model.py` - churn prediction model logic.
- `backend/app/services/ml/model_trainer.py` - training orchestration.
- `backend/app/services/ml/model_registry.py` - model registry abstraction.
- `backend/app/services/ml/explainability.py` - SHAP/explainability support.
- `backend/ml/training/train_models.py` - training entry point.
- `backend/ml/inference/predict.py` - inference entry point.

Configured model artifact paths default to:

```text
./ml/models/credit_model.pkl
./ml/models/default_model.pkl
./ml/models/churn_model.pkl
./ml/models/preprocessor.pkl
```

The settings layer also supports model version selection, model auto-loading, train/validation/test split ratios, a random seed, and Optuna trial count.

## External Data and Integrations

The connector package is intended to isolate external dataset dependencies from the rest of the application:

- Kaggle connector.
- World Bank connector.
- Macroeconomic connector.
- Government data connector.
- Generic external dataset connector.

Supported or planned integration areas include:

- Supabase PostgreSQL and object storage.
- World Bank API.
- Kaggle datasets.
- M-Pesa API credentials and callback URLs.
- Future Redis, Celery, Kafka, MLflow, feature store, and credit bureau integrations.

## Configuration

Configuration is environment-variable driven through `backend/app/config.py`. Start from the sample file:

```bash
cd backend
cp .env.example .env
```

### Required settings

| Variable | Description |
| --- | --- |
| `SECRET_KEY` | JWT signing secret. Use a strong random value in production. |
| `DATABASE_URL` | Async SQLAlchemy database URL, usually `postgresql+asyncpg://...`. |
| `DATABASE_URL_SYNC` | Sync database URL for Alembic migrations, usually `postgresql://...`. |
| `SUPABASE_URL` | Supabase project URL. |
| `SUPABASE_KEY` | Supabase anonymous/public key. |
| `SUPABASE_SERVICE_KEY` | Supabase service-role key. Treat as highly sensitive. |

### Common optional settings

| Variable | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `KenyaLendIntelligence` | Application display name. |
| `APP_VERSION` | `0.1.0` | Application version returned by utility endpoints. |
| `ENVIRONMENT` | `development` | Controls docs availability and production middleware behavior. |
| `DEBUG` | `false` | Debug mode flag. |
| `CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed browser origins. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime. |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime. |
| `LOG_LEVEL` | `INFO` | Logging verbosity. |
| `LOG_FORMAT` | `json` | Logging output format. |
| `MODEL_PATH` | `./ml/models` | Base directory for ML artifacts. |
| `WORLD_BANK_API_URL` | `https://api.worldbank.org/v2` | World Bank API base URL. |

### Production secrets guidance

Never commit real `.env` files, Supabase service-role keys, database passwords, JWT secrets, M-Pesa credentials, Kaggle API keys, model artifacts containing sensitive training data, or customer statements.

## Prerequisites

- Python 3.11 or newer.
- PostgreSQL 15 or compatible hosted PostgreSQL.
- Docker and Docker Compose, if using containers.
- Supabase project credentials if exercising storage-backed workflows.
- Optional Kaggle API credentials for Kaggle dataset fetching.

## Quick Start: Local Python Environment

From the repository root:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` so `DATABASE_URL`, `DATABASE_URL_SYNC`, `SECRET_KEY`, and Supabase settings match your environment.

Run migrations:

```bash
alembic upgrade head
```

Start the API:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open:

- `http://localhost:8000/health`
- `http://localhost:8000/api/docs`

## Quick Start: Docker Compose

The Compose file under `backend/` starts the API, PostgreSQL, and Redis.

```bash
cd backend
cp .env.example .env
# Edit .env with Supabase values if needed.
docker compose up --build
```

Then visit:

- API: `http://localhost:8000`
- Health: `http://localhost:8000/health`
- Swagger UI: `http://localhost:8000/api/docs`
- PostgreSQL: `localhost:5432`
- Redis: `localhost:6379`

To stop services:

```bash
docker compose down
```

To remove local database and Redis volumes:

```bash
docker compose down -v
```

## Database Migrations

Alembic is configured in `backend/alembic.ini` with migration scripts in `backend/alembic/`.

Common commands:

```bash
cd backend
alembic upgrade head
alembic downgrade -1
alembic revision --autogenerate -m "describe change"
alembic current
alembic history
```

The first migration creates the user, customer, loan, transaction, churn prediction, segment, and retention action tables.

## Authentication and Authorization

The API uses JWT bearer authentication:

1. Register a user.
2. Log in using OAuth2 password form data where `username` is the user's email.
3. Use the returned access token in the `Authorization: Bearer <token>` header.
4. Refresh access tokens with the refresh endpoint.

Role-aware dependencies exist for protected workflows such as dataset upload, which requires a data-scientist-style authorization dependency.

Example login request:

```bash
curl -X POST http://localhost:8000/api/v1/auth/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=analyst@example.com" \
  -d "password=your-password"
```

Example authenticated request:

```bash
curl http://localhost:8000/api/v1/customers/customers \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

## Running Tests and Quality Checks

From `backend/`:

```bash
pytest
pytest --cov=app --cov-report=term-missing
black --check app tests
isort --check-only app tests
flake8 app tests
mypy app
```

Tests live in `backend/tests/` and currently cover authentication, customers, loans, and churn-related behavior.

## Deployment

A Render blueprint is provided in `render.yaml`. It defines:

- A Docker-backed web service named `kenya-lend-intelligence-api`.
- A Render-managed PostgreSQL database named `kenya-lend-db`.
- `/health` as the health check path.
- Environment variables for app metadata, database URLs, Supabase credentials, model path, and logging.

High-level Render deployment flow:

1. Push the repository to GitHub.
2. Create or update the Render blueprint from `render.yaml`.
3. Set secret environment variables that are marked `sync: false`.
4. Confirm database connection strings are compatible with async application access and sync Alembic migrations.
5. Run migrations against the production database.
6. Verify `/health` returns `status: healthy`.

See `DEPLOYMENT.md` for deployment-specific notes as the project evolves.

## Operational Notes

- In development, Swagger UI and ReDoc are enabled. In production, docs and OpenAPI JSON are disabled by the settings in `backend/app/main.py`.
- Production trusted-host middleware currently allows `*.kenyalend.co.ke` and `kenyalend.co.ke`.
- Structured logging is configured through the app's logging utilities.
- Redis, Celery, Kafka, and MLflow are represented as future/planned services in code comments or Compose scaffolding.
- Several analytics endpoints currently return generated placeholder trend/distribution data until historical metrics are fully implemented.

## Development Workflow

Recommended workflow:

1. Create a branch for your change.
2. Set up the backend environment.
3. Add or update tests for behavior changes.
4. Run tests and quality checks.
5. Run the API locally and review generated docs.
6. Create an Alembic migration for database model changes.
7. Keep API schemas, services, repositories, and tests aligned.

### Coding conventions

- Use Python 3.11+ syntax.
- Keep FastAPI routers thin; put business logic in `app/services`.
- Keep database access in repositories where possible.
- Use Pydantic schemas for request and response validation.
- Prefer explicit, typed service interfaces.
- Do not commit secrets, `.env`, generated caches, or local virtual environments.

## Security and Compliance Considerations

Because this project is intended for lending and customer intelligence, production usage should include careful security, privacy, and model governance controls:

- Store secrets in a managed secret store or platform-provided environment variables.
- Rotate JWT secrets, Supabase service keys, database credentials, and M-Pesa credentials regularly.
- Encrypt sensitive customer statements and model artifacts at rest.
- Restrict access to raw statements, national IDs, phone numbers, credit decisions, and prediction explanations.
- Log only necessary metadata; avoid logging full statements, passwords, tokens, service keys, or national IDs.
- Add audit trails for credit decision changes and manual overrides.
- Validate uploaded statement files for type, size, malware, and parsing safety.
- Monitor models for drift, disparate impact, calibration, and degradation.
- Keep human review in the loop for borderline or adverse lending decisions.
- Align deployments with applicable Kenyan data protection, consumer protection, and financial services requirements.

## Roadmap

Planned or scaffolded improvements include:

- Token blacklist and stronger logout semantics.
- Forgot password, reset password, email verification, and MFA endpoints.
- Bulk customer import, merge, KYC upload, and export endpoints.
- Repayment schedules, collection workflows, and loan restructuring.
- Real-time churn webhooks, intervention triggers, and cohort analysis.
- Credit bureau integration and alternative-data scoring.
- Statement verification, fraud detection, and statement comparison.
- Dataset quality scoring, lineage, and automated refresh scheduling.
- Redis connection pooling, Celery workers, Kafka event publishing, and MLflow registry support.
- Feature store support and model registry integration.
- Production-ready observability dashboards and alerting.

## Troubleshooting

### The app fails during settings import

Verify `.env` exists and includes all required settings. If you run from the repository root instead of `backend/`, either run with the correct working directory or set `ENV_FILE=backend/.env`.

### Database connection errors

Check that:

- PostgreSQL is running.
- `DATABASE_URL` uses the async driver (`postgresql+asyncpg://`).
- `DATABASE_URL_SYNC` uses the sync driver (`postgresql://`).
- Username, password, host, port, and database name are correct.
- Network access is allowed for hosted databases.

### Alembic migration errors

Check that:

- You are running commands from `backend/`.
- `DATABASE_URL_SYNC` is present.
- The database user has permission to create tables and extensions.
- Existing schema state matches the migration history.

### Docker Compose does not start

Check that:

- Docker is running.
- Ports `8000`, `5432`, and `6379` are available.
- `.env` exists in `backend/` if Compose references Supabase variables.
- The Docker network driver in `backend/docker-compose.yml` is valid for your Docker version.

### API paths appear duplicated

Several routers define a router-level prefix and are also mounted with a domain prefix in `backend/app/main.py`. For example, the auth router is mounted at `/api/v1/auth` and also defines `/auth`, resulting in `/api/v1/auth/auth/...`. Use the generated OpenAPI docs as the source of truth for the current running application.

## Contributing

Contributions should keep the project modular, typed, and testable.

Before opening a pull request:

```bash
cd backend
pytest
black --check app tests
isort --check-only app tests
flake8 app tests
mypy app
```

For database changes, include an Alembic migration. For API changes, update this README and any relevant API documentation.

## License
