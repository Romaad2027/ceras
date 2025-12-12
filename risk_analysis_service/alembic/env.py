from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

from pathlib import Path
import sys
import os

                                                                        
sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from risk_analysis_service.db.models.base import Base

                                                                     
                                                         
from risk_analysis_service.db.models.audit_event import AuditEvent              
from risk_analysis_service.db.models.risk import Risk              
from risk_analysis_service.db.models.security_alert import SecurityAlert              
from risk_analysis_service.db.models.entity_profile import EntityProfile              
from risk_analysis_service.db.models.cloud_resource import CloudResource              
from risk_analysis_service.db.models.organization import Organization, User              
from risk_analysis_service.db.models.user_invitation import UserInvitation              
from risk_analysis_service.db.models.cloud_identity import CloudIdentity              
from risk_analysis_service.db.models.cloud_account import CloudAccount              

                                                   
                                                   
config = context.config

                                               
                                      
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

                                       
                            
                           
                                         

target_metadata = Base.metadata

                                                                             
db_url_override = os.getenv("DATABASE_URL")
if db_url_override:
    config.set_main_option("sqlalchemy.url", db_url_override)

                                                               
                  
                                                                     
          


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
