"""Script to create database tables directly via Supabase client."""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.logging import get_logger, setup_logging
from app.core.supabase import supabase

setup_logging()
logger = get_logger(__name__)

async def create_tables():
    """
    Attempts to create the microbiota_reports table using the RPC/SQL gateway.
    Note: This depends on the Supabase Key permissions.
    """
    logger.info("🚀 Checking database schema for Hierarchy (Companies/Collaborators)...")

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

    -- Special case: If column doesn't exist but table does (migration)
    DO $$ 
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name='microbiota_reports' AND column_name='company_id') THEN
            ALTER TABLE public.microbiota_reports ADD COLUMN company_id UUID REFERENCES public.companies(id) ON DELETE SET NULL;
        END IF;
    END $$;

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
        logger.info("Checking database schema status...")
        
        missing_stuff = False
        
        # 1. Check companies table
        try:
            supabase.table("companies").select("id").limit(1).execute()
            logger.info("✅ Table 'companies' exists.")
        except Exception:
            logger.warning("❌ Table 'companies' is missing.")
            missing_stuff = True

        # 2. Check collaborators table
        try:
            supabase.table("collaborators").select("id").limit(1).execute()
            logger.info("✅ Table 'collaborators' exists.")
        except Exception:
            logger.warning("❌ Table 'collaborators' is missing.")
            missing_stuff = True

        # 3. Check company_id column in reports
        try:
            supabase.table("microbiota_reports").select("company_id").limit(1).execute()
            logger.info("✅ Column 'company_id' exists in 'microbiota_reports'.")
        except Exception:
            logger.warning("❌ Column 'company_id' is missing in 'microbiota_reports'.")
            missing_stuff = True

        if missing_stuff:
            logger.error("❌ Database schema is OUTDATED.")
            logger.info("Please run the following SQL in your Supabase Dashboard -> SQL Editor:")
            print("\n" + "="*50)
            print(sql)
            print("="*50 + "\n")
        else:
            logger.info("🚀 Database schema is fully ALIGNED.")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(create_tables())
