# Initial migration - create all tables.

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('email', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), default='USER', nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create customers table
    op.create_table(
        'customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('national_id', sa.String(20), unique=True, nullable=False, index=True),
        sa.Column('location', sa.String(100), nullable=True),
        sa.Column('occupation', sa.String(255), nullable=True),
        sa.Column('employment_status', sa.String(50), default='INFORMAL'),
        sa.Column('income', sa.Float, nullable=True),
        sa.Column('customer_since', sa.Date, server_default=sa.text('CURRENT_DATE')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create loans table
    op.create_table(
        'loans',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('interest_rate', sa.Float, nullable=False),
        sa.Column('outstanding_balance', sa.Float, default=0.0),
        sa.Column('days_past_due', sa.Integer, default=0),
        sa.Column('status', sa.String(50), default='PENDING', nullable=False, index=True),
        sa.Column('approved_amount', sa.Float, nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('disbursed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('predicted_default_probability', sa.Float, nullable=True),
        sa.Column('credit_score_at_application', sa.Integer, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create customer_activity table
    op.create_table(
        'customer_activity',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('login_date', sa.Date, server_default=sa.text('CURRENT_DATE'), index=True),
        sa.Column('session_duration', sa.Integer, default=0),
        sa.Column('app_opens', sa.Integer, default=0),
        sa.Column('feature_usage', postgresql.JSONB, default={}),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('notification_opens', sa.Integer, default=0),
        sa.Column('engagement_score', sa.Float, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create mpesa_transactions table
    op.create_table(
        'mpesa_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('balance', sa.Float, nullable=True),
        sa.Column('reference', sa.String(100), nullable=True, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create bank_transactions table
    op.create_table(
        'bank_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('amount', sa.Float, nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('balance', sa.Float, nullable=True),
        sa.Column('account_number_masked', sa.String(20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create churn_predictions table
    op.create_table(
        'churn_predictions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('probability_of_churn', sa.Float, nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False, index=True),
        sa.Column('prediction_date', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), index=True),
        sa.Column('model_version', sa.String(50), nullable=False),
        sa.Column('features_snapshot', postgresql.JSONB, default={}),
        sa.Column('shap_values', postgresql.JSONB, default={}),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create customer_segments table
    op.create_table(
        'customer_segments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('segment', sa.String(50), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    
    # Create retention_actions table
    op.create_table(
        'retention_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('customers.id'), nullable=False, index=True),
        sa.Column('action_type', sa.String(100), nullable=False, index=True),
        sa.Column('status', sa.String(50), default='PENDING', nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('outcome', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )


def downgrade() -> None:
    op.drop_table('retention_actions')
    op.drop_table('customer_segments')
    op.drop_table('churn_predictions')
    op.drop_table('bank_transactions')
    op.drop_table('mpesa_transactions')
    op.drop_table('customer_activity')
    op.drop_table('loans')
    op.drop_table('customers')
    op.drop_table('users')