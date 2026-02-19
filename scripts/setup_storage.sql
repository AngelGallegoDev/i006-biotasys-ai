-- 🗄️ Configuración de Supabase Storage para Biotasys

-- 1. Crear el bucket 'reports' si no existe
-- Nota: Esto se puede hacer desde la UI de Supabase, pero aquí está el SQL.
-- INSERT INTO storage.buckets (id, name, public) 
-- VALUES ('reports', 'reports', true)
-- ON CONFLICT (id) DO NOTHING;

-- 2. Políticas de Seguridad (RLS) para el bucket 'reports'

-- Permitir que CUALQUIERA lea los informes (Necesario para que el Engine los descargue vía URL pública)
CREATE POLICY "Reports are publicly accessible" 
ON storage.objects FOR SELECT 
USING ( bucket_id = 'reports' );

-- Permitir subidas (Simulamos Backend A / Sandbox)
-- En producción, esto debería estar restringido a usuarios autenticados o service role.
-- Para desarrollo/Sandbox, permitimos anon upload:
CREATE POLICY "Allow public upload to reports bucket" 
ON storage.objects FOR INSERT 
WITH CHECK ( bucket_id = 'reports' );

-- Permitir borrar (Limpieza)
CREATE POLICY "Allow public update/delete" 
ON storage.objects FOR ALL 
USING ( bucket_id = 'reports' );
