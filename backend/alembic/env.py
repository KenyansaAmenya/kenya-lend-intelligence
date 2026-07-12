# Alembic Migration Environment.

import asyncio
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import AsyncEngine

from alembic import context

# Import application settings and models
from app.config import settings
from app.models import Base
from app.core.logging_config import get_logger


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


logger = get_logger(__name__)

config = context.config

target_metadata = Base.metadata

# Override sqlalchemy.url with settings
config.set_main_option("sqlalchemy.url", settings.database_url_sync)


def include_object(object, name, type_, reflected, compare_to):
    return True

def include_schemas(schema, name):
    return True

def run_migrations_offline() -> None:
    logger.info("Running migrations in OFFLINE mode")
    
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Batch mode for large datasets
        batch_mode=True,
        # Include all schemas
        include_schemas=True,
        # Include all objects
        include_object=include_object,
    )

    with context.begin_transaction():
        context.run_migrations()
    
    logger.info("Offline migrations completed successfully")


def do_run_migrations(connection):
    logger.info("Configuring migration context")
    
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # Transaction per migration for safety
        transaction_per_migration=True,
        # Compare types to detect changes
        compare_type=True,
        # Compare server defaults
        compare_server_default=True,
        # Include all schemas
        include_schemas=True,
        # Include all objects
        include_object=include_object,
        # Version table configuration
        version_table="alembic_version",
        version_table_schema="public",
        # Batch mode for large datasets
        batch_mode=True,
    )
    
    logger.info("Running migrations in transaction")
    
    with context.begin_transaction():
        context.run_migrations()
    
    logger.info("Migrations executed successfully")


def validate_migration():
    from sqlalchemy import text
    
    try:
        # Get sync engine for validation
        from app.core.database import sync_engine
        
        with sync_engine.connect() as conn:
            # Test database connection
            conn.execute(text("SELECT 1"))
            logger.info("Database connection validated")
            
            # Get current version
            result = conn.execute(
                text("SELECT version_num FROM alembic_version ORDER BY version_num DESC LIMIT 1")
            )
            version = result.scalar()
            if version:
                logger.info(f"Current schema version: {version}")
            else:
                logger.info("No existing version found (fresh database)")
                
    except Exception as e:
        logger.error(f"Migration validation failed: {e}")
        raise RuntimeError(f"Migration validation failed: {e}")


def run_migrations_with_rollback(connection):
    try:
        do_run_migrations(connection)
    except Exception as e:
        logger.error(f"Migration failed, rolling back: {e}")
        raise


async def run_migrations_online() -> None:
    logger.info("Running migrations in ONLINE mode")
    
    # Validate before running
    validate_migration()
    
    # Create async engine
    connectable = AsyncEngine(
        engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
            future=True,
        )
    )
    
    logger.info("Async engine created")
    
    try:
        # Run migrations
        async with connectable.connect() as connection:
            logger.info("Connected to database")
            await connection.run_sync(run_migrations_with_rollback)
            logger.info("Migrations applied successfully")
    
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    
    finally:
        # Dispose of the engine
        await connectable.dispose()
        logger.info("Database connection closed")


def run_migrations() -> None:
    logger.info("=" * 60)
    logger.info("ALEMBIC MIGRATION START")
    logger.info(f"Target database: {settings.database_url_sync}")
    logger.info("=" * 60)
    
    try:
        if context.is_offline_mode():
            run_migrations_offline()
        else:
            asyncio.run(run_migrations_online())
        
        logger.info("=" * 60)
        logger.info("ALEMBIC MIGRATION COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error("ALEMBIC MIGRATION FAILED")
        logger.error(f"Error: {e}")
        logger.error("=" * 60)
        raise


if __name__ == "__main__":
    run_migrations()

# Alembic entry point
run_migrations()