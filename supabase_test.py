import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load the variables from your .env file
load_dotenv()

# Get the URL and Key
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")

try:
    # Try to connect to Supabase
    supabase: Client = create_client(url, key)
    print("✅ Supabase Client Initialized Successfully!")
    print("URL:", url)
    
    # Optional: If you have already created a table in Supabase, uncomment the lines below 
    # and replace 'your_table_name' to test actually pulling data!
    
    response = supabase.table("institutions_data").select("*").limit(1).execute()
    print("✅ Database is responding! Data:", response.data)

except Exception as e:
    print(f"❌ Error connecting to Supabase: {e}")