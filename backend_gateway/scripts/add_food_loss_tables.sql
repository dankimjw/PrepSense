-- Food Loss and Waste (FLW) Database Integration
-- FAO Platform on Food Loss and Waste data schema

-- Main table for food loss rates by commodity and stage
CREATE TABLE IF NOT EXISTS food_loss_rates (
    id SERIAL PRIMARY KEY,
    cpc_code VARCHAR(10) NOT NULL,  -- CPC 2.1 commodity code
    commodity_name VARCHAR(255) NOT NULL,
    commodity_group VARCHAR(100),  -- e.g., 'Fruits & Vegetables', 'Cereals'
    stage VARCHAR(50) NOT NULL,  -- 'consumer', 'retail', 'processing', 'storage', 'farm'
    median_loss_pct DECIMAL(5,2),  -- Median loss percentage
    mean_loss_pct DECIMAL(5,2),  -- Mean loss percentage
    min_loss_pct DECIMAL(5,2),
    max_loss_pct DECIMAL(5,2),
    observations INT,  -- Number of data points
    country VARCHAR(100),  -- Can be specific country or 'Global'
    region VARCHAR(100),  -- Geographic region
    year_range VARCHAR(20),  -- e.g., '2015-2020'
    data_quality VARCHAR(20),  -- 'high', 'medium', 'low' based on method
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cpc_code, stage, country)
);

-- Mapping table between CPC codes and our FDC food IDs
CREATE TABLE IF NOT EXISTS cpc_to_fdc_mapping (
    id SERIAL PRIMARY KEY,
    cpc_code VARCHAR(10) NOT NULL,
    fdc_id INTEGER,
    product_name VARCHAR(255),
    mapping_confidence VARCHAR(20) DEFAULT 'medium',  -- 'high', 'medium', 'low'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(cpc_code, fdc_id)
);

-- Cached waste risk scores for pantry items
CREATE TABLE IF NOT EXISTS pantry_waste_risk (
    id SERIAL PRIMARY KEY,
    pantry_item_id INTEGER NOT NULL REFERENCES pantry_items(id),
    product_id INTEGER REFERENCES products(product_id),
    base_loss_rate DECIMAL(5,2),  -- From FLW database
    adjusted_loss_rate DECIMAL(5,2),  -- Adjusted for storage conditions
    days_until_expiry INTEGER,
    waste_risk_score DECIMAL(5,2),  -- Combined score (0-100)
    risk_category VARCHAR(20),  -- 'very_high', 'high', 'medium', 'low'
    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(pantry_item_id)
);

-- Historical waste tracking for users
CREATE TABLE IF NOT EXISTS user_food_waste (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    product_id INTEGER REFERENCES products(product_id),
    cpc_code VARCHAR(10),
    quantity_wasted DECIMAL(10,2),
    unit VARCHAR(20),
    reason VARCHAR(100),  -- 'expired', 'spoiled', 'excess', 'other'
    estimated_value DECIMAL(10,2),  -- Dollar value
    ghg_impact DECIMAL(10,2),  -- kg CO2e
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_flr_cpc_stage ON food_loss_rates(cpc_code, stage);
CREATE INDEX idx_flr_commodity_group ON food_loss_rates(commodity_group);
CREATE INDEX idx_cpc_fdc_mapping ON cpc_to_fdc_mapping(fdc_id);
CREATE INDEX idx_pwr_risk_score ON pantry_waste_risk(waste_risk_score DESC);
CREATE INDEX idx_ufw_user_date ON user_food_waste(user_id, recorded_at DESC);

-- Comments for documentation
COMMENT ON TABLE food_loss_rates IS 'FAO Food Loss and Waste data by commodity and supply chain stage';
COMMENT ON TABLE cpc_to_fdc_mapping IS 'Maps CPC 2.1 commodity codes to FoodData Central IDs';
COMMENT ON TABLE pantry_waste_risk IS 'Real-time waste risk scores for pantry items';
COMMENT ON TABLE user_food_waste IS 'Historical tracking of food waste by users';