from app.core.supabase import supabase

try:
    # Try to get one row to see keys
    res = supabase.table("microbiota_reports").select("*").limit(1).execute()
    if res.data:
        print(f"Columns found: {list(res.data[0].keys())}")
    else:
        print("Table is empty, trying to get columns from error if possible or just listing table info")
        # Alternative: run an insert with wrong key and capture error? No, too messy.
        # Let's try to just select id and see if it works
        res = supabase.table("microbiota_reports").select("id").limit(1).execute()
        print("Table exists and has 'id' column.")
except Exception as e:
    print(f"Error: {e}")
