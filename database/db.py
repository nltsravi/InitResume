import os
import getpass
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to current OS user and standard postgres DB for local macOS installations
current_user = getpass.getuser()

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"postgresql://{current_user}@localhost:5432/postgres"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    """
    Dependency helper to fetch a database session.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
