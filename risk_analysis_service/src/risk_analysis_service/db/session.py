from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy_utils import database_exists, create_database
import logging

db_username = "postgres"
db_password = "postgres"
db_host = "localhost"
db_port = "5432"
db_name = "risk_analysis_service"

connection_string = (
    f"postgresql+psycopg2://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
)

logger = logging.getLogger("risk_analysis.db")

if not database_exists(connection_string):
    create_database(connection_string)

engine = create_engine(connection_string)

try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        logger.info("Database connection OK: %s", result.scalar())
except Exception as e:
    logger.exception("Error connecting to PostgreSQL: %s", e)


                                        
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
