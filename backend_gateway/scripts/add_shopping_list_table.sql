-- Add shopping list table to PostgreSQL schema

-- Create shopping_list_items table
CREATE TABLE IF NOT EXISTS shopping_list_items (
    shopping_list_item_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    item_name VARCHAR(255) NOT NULL,
    quantity NUMERIC(10,2),
    unit VARCHAR(50),
    category VARCHAR(100),
    recipe_name VARCHAR(255),
    notes TEXT,
    is_checked BOOLEAN DEFAULT FALSE,
    priority INTEGER DEFAULT 0, -- 0=normal, 1=high, 2=urgent
    added_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_shopping_list_user_id ON shopping_list_items(user_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_added_date ON shopping_list_items(added_date);
CREATE INDEX IF NOT EXISTS idx_shopping_list_category ON shopping_list_items(category);

-- Create trigger to update updated_at
CREATE OR REPLACE FUNCTION update_shopping_list_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER shopping_list_update_timestamp
    BEFORE UPDATE ON shopping_list_items
    FOR EACH ROW
    EXECUTE FUNCTION update_shopping_list_updated_at();

-- Create a view for shopping list with item counts per user
CREATE OR REPLACE VIEW user_shopping_list_summary AS
SELECT 
    u.user_id,
    u.username,
    COUNT(sli.shopping_list_item_id) as total_items,
    COUNT(CASE WHEN sli.is_checked = false THEN 1 END) as unchecked_items,
    COUNT(CASE WHEN sli.is_checked = true THEN 1 END) as checked_items,
    MAX(sli.added_date) as last_added
FROM users u
LEFT JOIN shopping_list_items sli ON u.user_id = sli.user_id
GROUP BY u.user_id, u.username;