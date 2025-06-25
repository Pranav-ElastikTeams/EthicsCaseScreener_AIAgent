from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from db.models import Base
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Fetch database URI from .env
DATABASE_URI = os.getenv('DATABASE_URI')

if not DATABASE_URI:
    raise ValueError("DATABASE_URI is not set in the environment variables.")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URI, echo=True)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency to get DB session
def get_db_session():
    db = SessionLocal()
    return db

# Initialize DB with models
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print("Database initialized successfully.")
    except OperationalError as e:
        print(f"Error initializing the database: {e}")
