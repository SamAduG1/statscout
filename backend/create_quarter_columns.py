"""
Simple script to create quarter stat columns using SQLAlchemy
"""
import os
os.environ['DATABASE_URL'] = 'postgresql://postgres.tqyzxwogjhehjcwhxnre:Softwareidk5852!@aws-1-us-east-2.pooler.supabase.com:6543/postgres'

from models import Base, get_engine

def create_columns():
    """Create all model columns in database"""
    print("Creating quarter stat columns...")

    engine = get_engine()

    # This will add any missing columns (won't drop existing ones)
    Base.metadata.create_all(engine, checkfirst=True)

    print("✅ Done! Quarter columns created.")

if __name__ == "__main__":
    create_columns()
