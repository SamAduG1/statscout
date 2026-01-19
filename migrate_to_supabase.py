"""
Database Migration Script: Render PostgreSQL -> Supabase
Copies all tables and data from Render to Supabase
"""
import os
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker

def migrate_database(source_url, target_url):
    """
    Migrate entire database from source to target
    """
    print("=" * 60)
    print("DATABASE MIGRATION: Render -> Supabase")
    print("=" * 60)

    # Create engines
    print("\n[1/5] Connecting to source database (Render)...")
    source_engine = create_engine(source_url)

    print("[2/5] Connecting to target database (Supabase)...")
    target_engine = create_engine(target_url)

    # Get metadata from source
    print("[3/5] Reading source database schema...")
    source_metadata = MetaData()
    source_metadata.reflect(bind=source_engine)

    print(f"    Found {len(source_metadata.tables)} tables:")
    for table_name in source_metadata.tables.keys():
        print(f"      - {table_name}")

    # Create tables in target
    print("\n[4/5] Creating tables in target database...")
    source_metadata.create_all(target_engine)
    print("    [OK] Tables created successfully")

    # Copy data
    print("\n[5/5] Copying data...")
    source_conn = source_engine.connect()
    target_conn = target_engine.connect()

    for table_name, table in source_metadata.tables.items():
        print(f"\n  Copying table: {table_name}")

        # Read data from source
        result = source_conn.execute(table.select())
        rows = result.fetchall()
        print(f"    Found {len(rows)} rows")

        if len(rows) > 0:
            # Insert into target
            try:
                target_conn.execute(table.insert(), [dict(row._mapping) for row in rows])
                target_conn.commit()
                print(f"    [OK] Copied {len(rows)} rows successfully")
            except Exception as e:
                print(f"    [ERROR] Error copying data: {e}")
                target_conn.rollback()

    source_conn.close()
    target_conn.close()

    print("\n" + "=" * 60)
    print("MIGRATION COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Update your Render environment variable DATABASE_URL")
    print("2. Redeploy your backend")
    print("3. Test the connection")

if __name__ == "__main__":
    print("\nIMPORTANT: This script will copy ALL data from Render to Supabase")
    print("Make sure you have both connection strings ready.\n")

    # Get connection strings from user
    print("Enter your RENDER database URL:")
    print("(Should start with postgres:// or postgresql://)")
    render_url = input("Render URL: ").strip()

    print("\nEnter your SUPABASE database URL:")
    print("(Should start with postgresql://postgres...)")
    supabase_url = input("Supabase URL: ").strip()

    # Confirm before proceeding
    print("\n" + "=" * 60)
    print("Ready to migrate!")
    print("=" * 60)
    confirm = input("\nType 'YES' to proceed: ").strip()

    if confirm.upper() == "YES":
        try:
            migrate_database(render_url, supabase_url)
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {e}")
            print("\nTroubleshooting:")
            print("- Check that both URLs are correct")
            print("- Verify network connectivity")
            print("- Make sure SQLAlchemy is installed: pip install sqlalchemy psycopg2-binary")
    else:
        print("\nMigration cancelled.")
