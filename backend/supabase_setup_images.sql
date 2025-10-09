-- VOXY Agents - Image Management Setup
-- Execute este script no Supabase SQL Editor para configurar tabelas e policies

-- 1. Create user_images table
CREATE TABLE user_images (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    storage_path TEXT NOT NULL,
    original_name TEXT NOT NULL,
    content_type TEXT NOT NULL,
    file_size INTEGER NOT NULL,
    description TEXT,
    tags TEXT[],
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Create indexes for performance
CREATE INDEX idx_user_images_user_id ON user_images(user_id);
CREATE INDEX idx_user_images_created_at ON user_images(created_at DESC);
CREATE INDEX idx_user_images_public ON user_images(is_public) WHERE is_public = TRUE;
CREATE INDEX idx_user_images_tags ON user_images USING GIN(tags) WHERE tags IS NOT NULL;

-- 3. Enable Row Level Security
ALTER TABLE user_images ENABLE ROW LEVEL SECURITY;

-- 4. Create RLS Policies

-- Policy: Users can view their own images and public images
CREATE POLICY "Users can view own images and public images" ON user_images
FOR SELECT USING (
    user_id = auth.uid() OR is_public = TRUE
);

-- Policy: Users can insert their own images only
CREATE POLICY "Users can insert own images" ON user_images
FOR INSERT WITH CHECK (
    user_id = auth.uid()
);

-- Policy: Users can update their own images only
CREATE POLICY "Users can update own images" ON user_images
FOR UPDATE USING (
    user_id = auth.uid()
) WITH CHECK (
    user_id = auth.uid()
);

-- Policy: Users can delete their own images only
CREATE POLICY "Users can delete own images" ON user_images
FOR DELETE USING (
    user_id = auth.uid()
);

-- 5. Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_images_updated_at 
    BEFORE UPDATE ON user_images 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 6. Create storage bucket (if not exists)
-- Note: This needs to be done via Supabase Dashboard > Storage
-- Bucket name: "user-images"
-- Public: false (we'll handle public URLs via our API)

-- 7. Grant necessary permissions
GRANT ALL ON user_images TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

-- 8. Create helper function for image statistics (optional)
CREATE OR REPLACE FUNCTION get_user_image_stats(user_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_images', COUNT(*),
        'public_images', COUNT(*) FILTER (WHERE is_public = TRUE),
        'private_images', COUNT(*) FILTER (WHERE is_public = FALSE),
        'total_size_bytes', COALESCE(SUM(file_size), 0),
        'content_types', json_object_agg(content_type, cnt)
    ) INTO result
    FROM (
        SELECT 
            content_type,
            COUNT(*) as cnt,
            file_size,
            is_public
        FROM user_images 
        WHERE user_id = user_uuid
        GROUP BY content_type, file_size, is_public
    ) stats;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 9. Sample data for testing (optional - remove in production)
-- INSERT INTO user_images (user_id, storage_path, original_name, content_type, file_size, description, tags, is_public)
-- VALUES 
--   (auth.uid(), 'users/sample/test.jpg', 'test.jpg', 'image/jpeg', 12345, 'Sample image', ARRAY['test', 'sample'], false);

COMMENT ON TABLE user_images IS 'Stores metadata for user uploaded images with RLS policies for security';
COMMENT ON COLUMN user_images.storage_path IS 'Path to file in Supabase Storage bucket';
COMMENT ON COLUMN user_images.tags IS 'Array of lowercase tags for filtering and search';
COMMENT ON COLUMN user_images.is_public IS 'Whether image is publicly accessible via direct URL';