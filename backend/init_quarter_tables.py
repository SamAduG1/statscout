"""Initialize team quarter tables"""
from models import get_engine, init_db

engine = get_engine()
init_db(engine)
print("Database tables created successfully!")
