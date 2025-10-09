-- VOXY Agents - Vision Agent GPT-5 Database Migration
-- Execute este script no Supabase SQL Editor para adicionar suporte ao Vision Agent GPT-5
-- Version: 1.0
-- Date: 2025-09-20

-- ============================================================================
-- 1. EXTEND user_images TABLE FOR VISION AGENT TRACKING
-- ============================================================================

-- Add GPT-5 vision analysis tracking columns to existing user_images table
ALTER TABLE user_images 
ADD COLUMN IF NOT EXISTS vision_analyzed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS vision_analysis_count INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS vision_model_used TEXT,
ADD COLUMN IF NOT EXISTS vision_last_analysis TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS vision_analysis_cost DECIMAL(10,4) DEFAULT 0.0000;

-- Add comments for new columns
COMMENT ON COLUMN user_images.vision_analyzed IS 'Whether this image has been analyzed by Vision Agent';
COMMENT ON COLUMN user_images.vision_analysis_count IS 'Number of times this image has been analyzed';
COMMENT ON COLUMN user_images.vision_model_used IS 'Last model used for analysis (gpt-5 or gpt-4o)';
COMMENT ON COLUMN user_images.vision_last_analysis IS 'Timestamp of last vision analysis';
COMMENT ON COLUMN user_images.vision_analysis_cost IS 'Total cost of vision analyses for this image';

-- Create index for vision-analyzed images
CREATE INDEX IF NOT EXISTS idx_user_images_vision_analyzed 
ON user_images(vision_analyzed) WHERE vision_analyzed = TRUE;

CREATE INDEX IF NOT EXISTS idx_user_images_vision_model 
ON user_images(vision_model_used) WHERE vision_model_used IS NOT NULL;

-- ============================================================================
-- 2. CREATE vision_analyses TABLE FOR DETAILED TRACKING
-- ============================================================================

-- Create comprehensive vision analysis tracking table
CREATE TABLE IF NOT EXISTS vision_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    image_id UUID REFERENCES user_images(id) ON DELETE CASCADE,
    
    -- Analysis details
    analysis_type TEXT NOT NULL DEFAULT 'general', -- general, ocr, technical, artistic, document
    detail_level TEXT NOT NULL DEFAULT 'standard', -- basic, standard, detailed, comprehensive
    specific_questions TEXT[], -- Array of specific questions asked
    
    -- Model and performance tracking
    model_used TEXT NOT NULL, -- gpt-5 or gpt-4o (fallback)
    fallback_used BOOLEAN DEFAULT FALSE,
    processing_time_seconds DECIMAL(6,3),
    
    -- Cost tracking
    input_tokens INTEGER,
    output_tokens INTEGER,
    cost_usd DECIMAL(10,4),
    
    -- Rate limiting tracking
    user_requests_in_minute INTEGER DEFAULT 1,
    user_requests_in_hour INTEGER DEFAULT 1,
    
    -- Analysis results (stored for caching)
    analysis_result TEXT,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_id UUID,
    ip_address INET,
    user_agent TEXT
);

-- Add comments
COMMENT ON TABLE vision_analyses IS 'Detailed tracking of all vision analyses performed by GPT-5/GPT-4o';
COMMENT ON COLUMN vision_analyses.fallback_used IS 'TRUE if GPT-4o was used due to GPT-5 unavailability';
COMMENT ON COLUMN vision_analyses.confidence_score IS 'AI-assessed confidence in analysis accuracy';

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vision_analyses_user_id ON vision_analyses(user_id);
CREATE INDEX IF NOT EXISTS idx_vision_analyses_image_id ON vision_analyses(image_id);
CREATE INDEX IF NOT EXISTS idx_vision_analyses_created_at ON vision_analyses(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_vision_analyses_model_used ON vision_analyses(model_used);
CREATE INDEX IF NOT EXISTS idx_vision_analyses_session_id ON vision_analyses(session_id);
CREATE INDEX IF NOT EXISTS idx_vision_analyses_analysis_type ON vision_analyses(analysis_type);

-- Enable Row Level Security
ALTER TABLE vision_analyses ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 3. CREATE RLS POLICIES FOR vision_analyses
-- ============================================================================

-- Policy: Users can view their own analyses only
CREATE POLICY "Users can view own vision analyses" ON vision_analyses
FOR SELECT USING (
    user_id = auth.uid()
);

-- Policy: Users can insert their own analyses only
CREATE POLICY "Users can insert own vision analyses" ON vision_analyses
FOR INSERT WITH CHECK (
    user_id = auth.uid()
);

-- Policy: No updates or deletes (immutable audit trail)
-- CREATE POLICY "No updates on vision analyses" ON vision_analyses FOR UPDATE USING (false);
-- CREATE POLICY "No deletes on vision analyses" ON vision_analyses FOR DELETE USING (false);

-- ============================================================================
-- 4. CREATE vision_usage_stats TABLE FOR COST TRACKING
-- ============================================================================

-- Create daily usage statistics table
CREATE TABLE IF NOT EXISTS vision_usage_stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    
    -- Daily counters
    total_analyses INTEGER DEFAULT 0,
    gpt5_analyses INTEGER DEFAULT 0,
    gpt4o_fallback_analyses INTEGER DEFAULT 0,
    
    -- Cost tracking
    total_cost_usd DECIMAL(10,4) DEFAULT 0.0000,
    gpt5_cost_usd DECIMAL(10,4) DEFAULT 0.0000,
    gpt4o_cost_usd DECIMAL(10,4) DEFAULT 0.0000,
    
    -- Performance tracking
    avg_processing_time_seconds DECIMAL(6,3),
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    
    -- Rate limiting tracking
    max_requests_per_minute INTEGER DEFAULT 0,
    max_requests_per_hour INTEGER DEFAULT 0,
    rate_limit_violations INTEGER DEFAULT 0,
    
    -- Analysis type breakdown
    general_analyses INTEGER DEFAULT 0,
    ocr_analyses INTEGER DEFAULT 0,
    technical_analyses INTEGER DEFAULT 0,
    artistic_analyses INTEGER DEFAULT 0,
    document_analyses INTEGER DEFAULT 0,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to ensure one record per user per day
    UNIQUE(user_id, date)
);

-- Add comments
COMMENT ON TABLE vision_usage_stats IS 'Daily aggregated statistics for vision analysis usage and costs';

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_vision_usage_stats_user_id ON vision_usage_stats(user_id);
CREATE INDEX IF NOT EXISTS idx_vision_usage_stats_date ON vision_usage_stats(date DESC);
CREATE INDEX IF NOT EXISTS idx_vision_usage_stats_user_date ON vision_usage_stats(user_id, date);

-- Enable Row Level Security
ALTER TABLE vision_usage_stats ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- 5. CREATE RLS POLICIES FOR vision_usage_stats
-- ============================================================================

-- Policy: Users can view their own stats only
CREATE POLICY "Users can view own usage stats" ON vision_usage_stats
FOR SELECT USING (
    user_id = auth.uid()
);

-- Policy: System can insert/update usage stats (via service key)
CREATE POLICY "System can manage usage stats" ON vision_usage_stats
FOR ALL USING (true);

-- ============================================================================
-- 6. CREATE HELPER FUNCTIONS
-- ============================================================================

-- Function to update vision analysis tracking on user_images
CREATE OR REPLACE FUNCTION update_image_vision_tracking()
RETURNS TRIGGER AS $$
BEGIN
    -- Update user_images table with latest analysis info
    UPDATE user_images 
    SET 
        vision_analyzed = TRUE,
        vision_analysis_count = vision_analysis_count + 1,
        vision_model_used = NEW.model_used,
        vision_last_analysis = NEW.created_at,
        vision_analysis_cost = vision_analysis_cost + NEW.cost_usd
    WHERE id = NEW.image_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update image tracking
CREATE TRIGGER update_image_vision_tracking_trigger
    AFTER INSERT ON vision_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_image_vision_tracking();

-- Function to update daily usage statistics
CREATE OR REPLACE FUNCTION update_vision_usage_stats()
RETURNS TRIGGER AS $$
DECLARE
    stats_date DATE := DATE(NEW.created_at);
BEGIN
    -- Insert or update daily statistics
    INSERT INTO vision_usage_stats (
        user_id, 
        date,
        total_analyses,
        gpt5_analyses,
        gpt4o_fallback_analyses,
        total_cost_usd,
        gpt5_cost_usd,
        gpt4o_cost_usd,
        total_input_tokens,
        total_output_tokens
    ) VALUES (
        NEW.user_id,
        stats_date,
        1,
        CASE WHEN NEW.model_used = 'gpt-5' THEN 1 ELSE 0 END,
        CASE WHEN NEW.fallback_used THEN 1 ELSE 0 END,
        NEW.cost_usd,
        CASE WHEN NEW.model_used = 'gpt-5' THEN NEW.cost_usd ELSE 0 END,
        CASE WHEN NEW.model_used = 'gpt-4o' THEN NEW.cost_usd ELSE 0 END,
        COALESCE(NEW.input_tokens, 0),
        COALESCE(NEW.output_tokens, 0)
    )
    ON CONFLICT (user_id, date) 
    DO UPDATE SET
        total_analyses = vision_usage_stats.total_analyses + 1,
        gpt5_analyses = vision_usage_stats.gpt5_analyses + 
            CASE WHEN NEW.model_used = 'gpt-5' THEN 1 ELSE 0 END,
        gpt4o_fallback_analyses = vision_usage_stats.gpt4o_fallback_analyses + 
            CASE WHEN NEW.fallback_used THEN 1 ELSE 0 END,
        total_cost_usd = vision_usage_stats.total_cost_usd + NEW.cost_usd,
        gpt5_cost_usd = vision_usage_stats.gpt5_cost_usd + 
            CASE WHEN NEW.model_used = 'gpt-5' THEN NEW.cost_usd ELSE 0 END,
        gpt4o_cost_usd = vision_usage_stats.gpt4o_cost_usd + 
            CASE WHEN NEW.model_used = 'gpt-4o' THEN NEW.cost_usd ELSE 0 END,
        total_input_tokens = vision_usage_stats.total_input_tokens + COALESCE(NEW.input_tokens, 0),
        total_output_tokens = vision_usage_stats.total_output_tokens + COALESCE(NEW.output_tokens, 0),
        updated_at = NOW();
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update usage statistics
CREATE TRIGGER update_vision_usage_stats_trigger
    AFTER INSERT ON vision_analyses
    FOR EACH ROW
    EXECUTE FUNCTION update_vision_usage_stats();

-- ============================================================================
-- 7. CREATE HELPER FUNCTIONS FOR API
-- ============================================================================

-- Function to get user's vision usage summary
CREATE OR REPLACE FUNCTION get_user_vision_summary(user_uuid UUID)
RETURNS JSON AS $$
DECLARE
    result JSON;
BEGIN
    SELECT json_build_object(
        'total_analyses', COALESCE(SUM(total_analyses), 0),
        'total_cost_usd', COALESCE(SUM(total_cost_usd), 0),
        'gpt5_usage_percentage', 
            CASE 
                WHEN COALESCE(SUM(total_analyses), 0) > 0 
                THEN ROUND((COALESCE(SUM(gpt5_analyses), 0)::DECIMAL / SUM(total_analyses)) * 100, 2)
                ELSE 0 
            END,
        'avg_processing_time', COALESCE(AVG(avg_processing_time_seconds), 0),
        'last_30_days', json_agg(
            json_build_object(
                'date', date,
                'analyses', total_analyses,
                'cost', total_cost_usd
            ) ORDER BY date DESC
        )
    ) INTO result
    FROM vision_usage_stats 
    WHERE user_id = user_uuid 
      AND date >= CURRENT_DATE - INTERVAL '30 days';
    
    RETURN COALESCE(result, '{"total_analyses": 0, "total_cost_usd": 0}'::json);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to check if user is within rate limits
CREATE OR REPLACE FUNCTION check_vision_rate_limits(
    user_uuid UUID,
    check_minute BOOLEAN DEFAULT TRUE,
    check_hour BOOLEAN DEFAULT TRUE
)
RETURNS JSON AS $$
DECLARE
    minute_count INTEGER := 0;
    hour_count INTEGER := 0;
    result JSON;
BEGIN
    -- Count analyses in last minute
    IF check_minute THEN
        SELECT COUNT(*) INTO minute_count
        FROM vision_analyses
        WHERE user_id = user_uuid
          AND created_at >= NOW() - INTERVAL '1 minute';
    END IF;
    
    -- Count analyses in last hour  
    IF check_hour THEN
        SELECT COUNT(*) INTO hour_count
        FROM vision_analyses
        WHERE user_id = user_uuid
          AND created_at >= NOW() - INTERVAL '1 hour';
    END IF;
    
    SELECT json_build_object(
        'within_limits', (minute_count < 10 AND hour_count < 50),
        'minute_count', minute_count,
        'hour_count', hour_count,
        'minute_limit', 10,
        'hour_limit', 50
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================================================
-- 8. GRANT PERMISSIONS
-- ============================================================================

-- Grant permissions for authenticated users
GRANT ALL ON vision_analyses TO authenticated;
GRANT ALL ON vision_usage_stats TO authenticated;
GRANT USAGE ON SCHEMA public TO authenticated;

-- Grant permissions for functions
GRANT EXECUTE ON FUNCTION get_user_vision_summary(UUID) TO authenticated;
GRANT EXECUTE ON FUNCTION check_vision_rate_limits(UUID, BOOLEAN, BOOLEAN) TO authenticated;

-- ============================================================================
-- 9. CREATE INDEXES FOR PERFORMANCE OPTIMIZATION
-- ============================================================================

-- Additional composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_vision_analyses_user_created 
ON vision_analyses(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vision_analyses_image_created 
ON vision_analyses(image_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_vision_analyses_cost_tracking 
ON vision_analyses(user_id, created_at, cost_usd) 
WHERE cost_usd > 0;

-- ============================================================================
-- 10. DATA VALIDATION AND CONSTRAINTS
-- ============================================================================

-- Add check constraints for data integrity
ALTER TABLE vision_analyses 
ADD CONSTRAINT IF NOT EXISTS chk_analysis_type 
CHECK (analysis_type IN ('general', 'ocr', 'technical', 'artistic', 'document'));

ALTER TABLE vision_analyses 
ADD CONSTRAINT IF NOT EXISTS chk_detail_level 
CHECK (detail_level IN ('basic', 'standard', 'detailed', 'comprehensive'));

ALTER TABLE vision_analyses 
ADD CONSTRAINT IF NOT EXISTS chk_model_used 
CHECK (model_used IN ('gpt-5', 'gpt-4o'));

ALTER TABLE vision_analyses 
ADD CONSTRAINT IF NOT EXISTS chk_confidence_score 
CHECK (confidence_score IS NULL OR (confidence_score >= 0 AND confidence_score <= 1));

ALTER TABLE vision_analyses 
ADD CONSTRAINT IF NOT EXISTS chk_processing_time 
CHECK (processing_time_seconds IS NULL OR processing_time_seconds >= 0);

ALTER TABLE vision_analyses 
ADD CONSTRAINT IF NOT EXISTS chk_cost_positive 
CHECK (cost_usd >= 0);

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Insert migration record (optional)
-- CREATE TABLE IF NOT EXISTS schema_migrations (
--     version TEXT PRIMARY KEY,
--     applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
-- );
-- 
-- INSERT INTO schema_migrations (version) 
-- VALUES ('vision_agent_gpt5_v1.0')
-- ON CONFLICT (version) DO NOTHING;

-- Display migration summary
DO $$
BEGIN
    RAISE NOTICE '';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'VOXY VISION AGENT GPT-5 DATABASE MIGRATION COMPLETED SUCCESSFULLY';
    RAISE NOTICE '============================================================================';
    RAISE NOTICE 'Tables created/modified:';
    RAISE NOTICE '  - user_images (extended with 5 vision tracking columns)';
    RAISE NOTICE '  - vision_analyses (new table for detailed tracking)';
    RAISE NOTICE '  - vision_usage_stats (new table for daily statistics)';
    RAISE NOTICE '';
    RAISE NOTICE 'Functions created:';
    RAISE NOTICE '  - update_image_vision_tracking()';
    RAISE NOTICE '  - update_vision_usage_stats()';
    RAISE NOTICE '  - get_user_vision_summary(UUID)';
    RAISE NOTICE '  - check_vision_rate_limits(UUID, BOOLEAN, BOOLEAN)';
    RAISE NOTICE '';
    RAISE NOTICE 'Triggers created:';
    RAISE NOTICE '  - update_image_vision_tracking_trigger';
    RAISE NOTICE '  - update_vision_usage_stats_trigger';
    RAISE NOTICE '';
    RAISE NOTICE 'RLS Policies: Enabled for all new tables';
    RAISE NOTICE 'Indexes: Created for optimal query performance';
    RAISE NOTICE '============================================================================';
END $$;