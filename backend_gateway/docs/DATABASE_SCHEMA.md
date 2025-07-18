# PrepSense PostgreSQL Database Schema

This document provides a complete overview of the PrepSense PostgreSQL database schema, including all tables, columns, data types, and relationships.

## Overview

The PrepSense database is designed to support a food waste reduction application with the following core entities:
- **Users** - Application users with authentication and profile data
- **Pantries** - User-owned pantry containers
- **Pantry Items** - Individual food items with expiration tracking
- **Recipes** - Recipe storage and management
- **User Preferences** - Dietary preferences, allergens, and cuisine preferences

## Database Tables

### 1. Users Table
Primary table for user authentication and profile information.

```sql
users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_users_email` on `email`
- `idx_users_username` on `username`

### 2. Pantries Table
Container table for organizing pantry items by user.

```sql
pantries (
    pantry_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    pantry_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_pantries_user_id` on `user_id`

**Foreign Keys:**
- `user_id` → `users(user_id)`

### 3. Pantry Items Table
Core table for tracking individual food items with expiration dates, quantities, and metadata.

```sql
pantry_items (
    pantry_item_id SERIAL PRIMARY KEY,
    pantry_id INTEGER NOT NULL REFERENCES pantries(pantry_id) ON DELETE CASCADE,
    product_name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
    unit_of_measurement VARCHAR(50),
    expiration_date DATE,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    source VARCHAR(20) DEFAULT 'manual' CHECK (source IN ('manual', 'vision_detected', 'receipt_scan')),
    status VARCHAR(20) DEFAULT 'available' CHECK (status IN ('available', 'consumed', 'expired')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    consumed_at TIMESTAMP,
    used_quantity DECIMAL(10, 2) DEFAULT 0,
    metadata JSONB DEFAULT '{}'::jsonb
)
```

**Indexes:**
- `idx_pantry_items_pantry_id` on `pantry_id`
- `idx_pantry_items_expiration` on `expiration_date`
- `idx_pantry_items_status` on `status`
- `idx_pantry_items_category` on `category`
- `idx_pantry_items_metadata` GIN index on `metadata`

**Foreign Keys:**
- `pantry_id` → `pantries(pantry_id)`

**Check Constraints:**
- `source` must be one of: 'manual', 'vision_detected', 'receipt_scan'
- `status` must be one of: 'available', 'consumed', 'expired'

### 4. User Preferences Table
Stores user-specific preferences using JSONB for flexibility.

```sql
user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    household_size INTEGER DEFAULT 1,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Foreign Keys:**
- `user_id` → `users(user_id)` (UNIQUE constraint ensures 1:1 relationship)

### 5. User Dietary Preferences Table
Many-to-many relationship for user dietary preferences.

```sql
user_dietary_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    preference VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, preference)
)
```

**Foreign Keys:**
- `user_id` → `users(user_id)`

### 6. User Allergens Table
Many-to-many relationship for user allergens.

```sql
user_allergens (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    allergen VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, allergen)
)
```

**Foreign Keys:**
- `user_id` → `users(user_id)`

### 7. User Cuisine Preferences Table
Many-to-many relationship for user cuisine preferences.

```sql
user_cuisine_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cuisine VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, cuisine)
)
```

**Foreign Keys:**
- `user_id` → `users(user_id)`

### 8. Recipes Table
Stores recipe information with JSONB for flexible recipe data.

```sql
recipes (
    recipe_id SERIAL PRIMARY KEY,
    recipe_name VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100),
    prep_time INTEGER,
    cook_time INTEGER,
    servings INTEGER,
    difficulty VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    recipe_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_recipes_cuisine` on `cuisine_type`
- `idx_recipes_data` GIN index on `recipe_data`

**Check Constraints:**
- `difficulty` must be one of: 'easy', 'medium', 'hard'

### 9. Recipe Ingredients Table
Many-to-many relationship between recipes and ingredients.

```sql
recipe_ingredients (
    recipe_id INTEGER NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2),
    unit VARCHAR(50),
    is_optional BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (recipe_id, ingredient_name)
)
```

**Foreign Keys:**
- `recipe_id` → `recipes(recipe_id)`

### 10. User Recipes Table
Stores user-saved recipes with ratings and favorites.

```sql
user_recipes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    recipe_id INTEGER REFERENCES recipes(recipe_id),
    recipe_title VARCHAR(255) NOT NULL,
    recipe_image TEXT,
    recipe_data JSONB DEFAULT '{}'::jsonb,
    rating VARCHAR(20) DEFAULT 'neutral' CHECK (rating IN ('thumbs_up', 'thumbs_down', 'neutral')),
    is_favorite BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

**Indexes:**
- `idx_user_recipes_user_rating` on `(user_id, rating)`
- `idx_user_recipes_user_favorite` on `(user_id, is_favorite)`

**Foreign Keys:**
- `user_id` → `users(user_id)`
- `recipe_id` → `recipes(recipe_id)` (optional)

**Check Constraints:**
- `rating` must be one of: 'thumbs_up', 'thumbs_down', 'neutral'

## Database Views

### User Pantry Full View
Convenient view that joins pantry items with pantry information to get user context.

```sql
CREATE OR REPLACE VIEW user_pantry_full AS
SELECT 
    pi.pantry_item_id,
    pi.pantry_id,
    p.user_id,
    pi.product_name,
    pi.brand_name,
    pi.category,
    pi.quantity,
    pi.unit_of_measurement,
    pi.expiration_date,
    pi.unit_price,
    pi.total_price,
    pi.source,
    pi.status,
    pi.created_at,
    pi.updated_at,
    pi.metadata
FROM pantry_items pi
JOIN pantries p ON pi.pantry_id = p.pantry_id;
```

## Database Functions and Triggers

### Update Timestamp Trigger
Automatically updates the `updated_at` column when records are modified.

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';
```

**Applied to tables:**
- `users`
- `pantry_items`
- `user_preferences`
- `user_recipes`

## Default Data

### Demo User
A default demo user is created for testing purposes:

```sql
INSERT INTO users (user_id, username, email, first_name, last_name, role)
VALUES (111, 'demo_user', 'demo@prepsense.com', 'Demo', 'User', 'user');
```

### Default Pantry
A default pantry is created for the demo user:

```sql
INSERT INTO pantries (user_id, pantry_name)
SELECT 111, 'My Pantry'
WHERE NOT EXISTS (SELECT 1 FROM pantries WHERE user_id = 111);
```

## Key Features

### PostgreSQL-Specific Features
- **JSONB columns** for flexible metadata and preferences storage
- **GIN indexes** on JSONB columns for efficient querying
- **Check constraints** for data validation
- **Automatic timestamp triggers** for audit trails
- **Cascade deletes** for data integrity

### Performance Optimizations
- Strategic indexing on frequently queried columns
- Composite indexes for common query patterns
- JSONB storage for flexible schema evolution
- Efficient foreign key relationships

### Data Integrity
- Foreign key constraints ensure referential integrity
- Check constraints validate enum-like values
- Unique constraints prevent duplicate data
- Cascade deletes maintain consistency

## Usage Notes

1. **User ID 111** is reserved for the demo user
2. **JSONB metadata** in pantry_items can store flexible attributes like nutrition info, photos, etc.
3. **Expiration tracking** is handled through the `expiration_date` and `status` fields
4. **Recipe data** is stored as JSONB to accommodate various recipe formats (Spoonacular, custom, etc.)
5. **Preference system** supports multiple dietary restrictions, allergens, and cuisine preferences per user

This schema supports all core PrepSense functionality including user management, pantry tracking, recipe storage, and comprehensive user preferences with PostgreSQL-optimized features.
