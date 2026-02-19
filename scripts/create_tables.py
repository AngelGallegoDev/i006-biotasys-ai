"""Script to create database tables directly via Supabase client."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.logging import get_logger
from app.core.supabase import supabase

logger = get_logger(__name__)

async def create_tables():
    """
    Attempts to create the microbiota_reports table using the RPC/SQL gateway.
    Note: This depends on the Supabase Key permissions.
    """
    logger.info("🚀 Attempting to create table 'microbiota_reports' via SQL gateway...")

    sql = """
    -- 1. Companies Master Table
    CREATE TABLE IF NOT EXISTS public.companies (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- 2. Collaborators Master Table
    CREATE TABLE IF NOT EXISTS public.collaborators (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        company_id UUID REFERENCES public.companies(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        role TEXT,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- 3. Update/Create Microbiota Reports Table
    CREATE TABLE IF NOT EXISTS public.microbiota_reports (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        study_code TEXT NOT NULL,
        patient_id TEXT NOT NULL,
        user_id UUID REFERENCES public.collaborators(id) ON DELETE SET NULL,
        company_id UUID REFERENCES public.companies(id) ON DELETE SET NULL,
        report_data JSONB NOT NULL,
        created_at TIMESTAMPTZ DEFAULT now()
    );

    -- Enable RLS
    ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.collaborators ENABLE ROW LEVEL SECURITY;
    ALTER TABLE public.microbiota_reports ENABLE ROW LEVEL SECURITY;

    -- Basic development policies
    DO $$ 
    BEGIN
        -- Companies Policy
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Enable all for development' AND tablename = 'companies') THEN
            CREATE POLICY "Enable all for development" ON public.companies FOR ALL USING (true);
        END IF;
        
        -- Collaborators Policy
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Enable all for development' AND tablename = 'collaborators') THEN
            CREATE POLICY "Enable all for development" ON public.collaborators FOR ALL USING (true);
        END IF;

        -- Reports Policy
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Enable all for development' AND tablename = 'microbiota_reports') THEN
            CREATE POLICY "Enable all for development" ON public.microbiota_reports FOR ALL USING (true);
        END IF;
    END $$;
    """

    try:
        # We try to use the undocumented but often available _raw_sql or similar if possible,
        # but since 'supabase-py' is limited, we'll try to use a function or execute if available.
        # Most Supabase clients don't allow raw SQL for SECURITY reasons.
        # If this fails, we will know for sure we need the manual step or DATABASE_URL.

        # Alternative: try a dummy insert to see if it triggers an error that tells us something
        logger.warning("Supabase client generally restricts DDL (CREATE TABLE) via API for safety.")
        logger.info("Checking if table exists by doing a silent select...")

        try:
            supabase.table("microbiota_reports").select("id").limit(1).execute()
            logger.info("✅ Table already exists!")
        except Exception:
            logger.error("❌ Table does not exist and cannot be created via the REST API Key.")
            logger.info("Please run the following SQL in your Supabase Dashboard -> SQL Editor:")
            print("\n" + "="*50)
            print(sql)
            print("="*50 + "\n")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_tables())
