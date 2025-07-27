-- Add user_recipes and pantry_history tables to PostgreSQL schema

-- Create user_recipes table
CREATE TABLE IF NOT EXISTS user_recipes (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipe_id INTEGER,
    recipe_title VARCHAR(255) NOT NULL,
    recipe_image TEXT,
    recipe_data JSONB NOT NULL,
    source VARCHAR(50) NOT NULL CHECK (source IN ('spoonacular', 'chat', 'manual', 'scan')),
    source_reference VARCHAR(255),
    rating VARCHAR(20) DEFAULT 'neutral' CHECK (rating IN ('loved', 'liked', 'neutral', 'disliked', 'never_again')),
    is_favorite BOOLEAN DEFAULT FALSE,
    notes TEXT,
    prep_time INTEGER,
    cook_time INTEGER,
    total_time INTEGER,
    servings INTEGER,
    difficulty VARCHAR(20) CHECK (difficulty IN ('easy', 'medium', 'hard', 'expert')),
    cuisine TEXT[],
    dish_type TEXT[],
    diet_labels TEXT[],
    tags TEXT[],
    times_cooked INTEGER DEFAULT 0,
    last_cooked_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for user_recipes
CREATE INDEX IF NOT EXISTS idx_user_recipes_user_id ON user_recipes(user_id);
CREATE INDEX IF NOT EXISTS idx_user_recipes_source ON user_recipes(source);
CREATE INDEX IF NOT EXISTS idx_user_recipes_is_favorite ON user_recipes(is_favorite);
CREATE INDEX IF NOT EXISTS idx_user_recipes_created_at ON user_recipes(created_at);
CREATE INDEX IF NOT EXISTS idx_user_recipes_recipe_id ON user_recipes(recipe_id);
CREATE INDEX IF NOT EXISTS idx_user_recipes_rating ON user_recipes(rating);

-- Create pantry_history table
CREATE TABLE IF NOT EXISTS pantry_history (
    history_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    pantry_item_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    change_type VARCHAR(50) NOT NULL CHECK (change_type IN ('added', 'consumed', 'updated', 'deleted', 'expired', 'recipe_used')),
    change_source VARCHAR(50) CHECK (change_source IN ('manual', 'recipe', 'scan', 'api', 'system')),
    recipe_name VARCHAR(255),
    recipe_id VARCHAR(255),
    quantity_before NUMERIC(10,2),
    used_quantity_before NUMERIC(10,2),
    quantity_after NUMERIC(10,2),
    used_quantity_after NUMERIC(10,2),
    quantity_changed NUMERIC(10,2),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    changed_by_user_id INTEGER REFERENCES users(user_id),
    transaction_id VARCHAR(255),
    notes TEXT
);

-- Create indexes for pantry_history
CREATE INDEX IF NOT EXISTS idx_pantry_history_user_id ON pantry_history(user_id);
CREATE INDEX IF NOT EXISTS idx_pantry_history_pantry_item_id ON pantry_history(pantry_item_id);
CREATE INDEX IF NOT EXISTS idx_pantry_history_change_type ON pantry_history(change_type);
CREATE INDEX IF NOT EXISTS idx_pantry_history_changed_at ON pantry_history(changed_at);
CREATE INDEX IF NOT EXISTS idx_pantry_history_recipe_id ON pantry_history(recipe_id);

-- Create trigger to update updated_at for user_recipes
CREATE OR REPLACE FUNCTION update_user_recipes_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER user_recipes_update_timestamp
    BEFORE UPDATE ON user_recipes
    FOR EACH ROW
    EXECUTE FUNCTION update_user_recipes_updated_at();

-- Create views for analytics

-- View for user recipe statistics
CREATE OR REPLACE VIEW user_recipe_stats AS
SELECT 
    u.user_id,
    u.username,
    COUNT(ur.id) as total_recipes,
    COUNT(CASE WHEN ur.is_favorite THEN 1 END) as favorite_recipes,
    COUNT(CASE WHEN ur.source = 'chat' THEN 1 END) as ai_generated_recipes,
    COUNT(CASE WHEN ur.source = 'spoonacular' THEN 1 END) as spoonacular_recipes,
    COUNT(CASE WHEN ur.rating = 'loved' THEN 1 END) as loved_recipes,
    SUM(ur.times_cooked) as total_times_cooked,
    MAX(ur.created_at) as last_recipe_added,
    MAX(ur.last_cooked_at) as last_cooked_date
FROM users u
LEFT JOIN user_recipes ur ON u.user_id = ur.user_id
GROUP BY u.user_id, u.username;

-- View for pantry consumption trends
CREATE OR REPLACE VIEW pantry_consumption_trends AS
SELECT 
    ph.user_id,
    DATE_TRUNC('week', ph.changed_at) as week,
    ph.change_type,
    COUNT(*) as change_count,
    SUM(ABS(ph.quantity_changed)) as total_quantity_changed
FROM pantry_history ph
WHERE ph.changed_at >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY ph.user_id, DATE_TRUNC('week', ph.changed_at), ph.change_type
ORDER BY week DESC;

-- Function to log pantry changes
CREATE OR REPLACE FUNCTION log_pantry_change()
RETURNS TRIGGER AS $$
BEGIN
    -- For UPDATE operations
    IF TG_OP = 'UPDATE' THEN
        -- Only log if quantity actually changed
        IF OLD.quantity != NEW.quantity OR OLD.used_quantity != NEW.used_quantity THEN
            INSERT INTO pantry_history (
                pantry_item_id,
                user_id,
                change_type,
                change_source,
                quantity_before,
                used_quantity_before,
                quantity_after,
                used_quantity_after,
                quantity_changed,
                notes
            )
            SELECT 
                NEW.pantry_item_id,
                p.user_id,
                CASE 
                    WHEN NEW.quantity < OLD.quantity THEN 'consumed'
                    WHEN NEW.quantity > OLD.quantity THEN 'added'
                    ELSE 'updated'
                END,
                'manual',
                OLD.quantity,
                OLD.used_quantity,
                NEW.quantity,
                NEW.used_quantity,
                NEW.quantity - OLD.quantity,
                'Automatic logging from trigger'
            FROM pantries p
            WHERE p.pantry_id = NEW.pantry_id;
        END IF;
        RETURN NEW;
    
    -- For INSERT operations
    ELSIF TG_OP = 'INSERT' THEN
        INSERT INTO pantry_history (
            pantry_item_id,
            user_id,
            change_type,
            change_source,
            quantity_before,
            quantity_after,
            quantity_changed,
            notes
        )
        SELECT 
            NEW.pantry_item_id,
            p.user_id,
            'added',
            'manual',
            0,
            NEW.quantity,
            NEW.quantity,
            'Item added to pantry'
        FROM pantries p
        WHERE p.pantry_id = NEW.pantry_id;
        RETURN NEW;
    
    -- For DELETE operations
    ELSIF TG_OP = 'DELETE' THEN
        INSERT INTO pantry_history (
            pantry_item_id,
            user_id,
            change_type,
            change_source,
            quantity_before,
            quantity_after,
            quantity_changed,
            notes
        )
        SELECT 
            OLD.pantry_item_id,
            p.user_id,
            'deleted',
            'manual',
            OLD.quantity,
            0,
            -OLD.quantity,
            'Item removed from pantry'
        FROM pantries p
        WHERE p.pantry_id = OLD.pantry_id;
        RETURN OLD;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for pantry_items changes
CREATE TRIGGER pantry_items_history_trigger
    AFTER INSERT OR UPDATE OR DELETE ON pantry_items
    FOR EACH ROW
    EXECUTE FUNCTION log_pantry_change();