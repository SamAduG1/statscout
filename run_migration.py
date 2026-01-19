"""
Simple wrapper to run migration with connection strings
Edit the URLs below and run this script
"""
from migrate_to_supabase import migrate_database

# EDIT THESE TWO LINES:
RENDER_URL = "postgresql://statscout:7cKBBW44O0ZfalLCZS5Tyu4GxhLnJmpI@dpg-d5bur8shg0os73duan60-a.ohio-postgres.render.com/statscout"
SUPABASE_URL = "postgresql://postgres:Softwareidk5852!@db.tqyzxwogjhehjcwhxnre.supabase.co:5432/postgres"

if __name__ == "__main__":
    if "PASTE_YOUR" in RENDER_URL or "PASTE_YOUR" in SUPABASE_URL:
        print("ERROR: Please edit run_migration.py and paste your connection strings first!")
        print("\nOpen run_migration.py and replace:")
        print("  - RENDER_URL with your Render PostgreSQL URL")
        print("  - SUPABASE_URL with your Supabase PostgreSQL URL")
    else:
        print("Starting migration...")
        print(f"From: {RENDER_URL[:30]}...")
        print(f"To:   {SUPABASE_URL[:30]}...")
        print()

        try:
            migrate_database(RENDER_URL, SUPABASE_URL)
        except Exception as e:
            print(f"\n[ERROR] Migration failed: {e}")
            import traceback
            traceback.print_exc()
