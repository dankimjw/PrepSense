#!/usr/bin/env python3
"""
Setup script for Cloud SQL PostgreSQL instance and database schema for PrepSense
"""

import os
import sys
import subprocess
from pathlib import Path

# Configuration
PROJECT_ID = "adsp-34002-on02-prep-sense"
INSTANCE_NAME = "prepsense-postgres"
REGION = "us-central1"
TIER = "db-f1-micro"  # Small instance for development
DATABASE_NAME = "prepsense"
ROOT_PASSWORD = "changeme123!"  # Change this!

def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result

def enable_required_apis():
    """Enable required APIs for Cloud SQL"""
    print("\n0. Enabling required APIs...")
    apis = [
        "sqladmin.googleapis.com",
        "compute.googleapis.com",
        "servicenetworking.googleapis.com",
        "iam.googleapis.com"  # For IAM authentication
    ]
    
    for api in apis:
        cmd = f"gcloud services enable {api} --project={PROJECT_ID}"
        print(f"Enabling {api}...")
        run_command(cmd)
    
    print("All required APIs enabled!")

def create_instance():
    """Create Cloud SQL PostgreSQL instance"""
    print(f"\n1. Creating Cloud SQL PostgreSQL instance '{INSTANCE_NAME}'...")
    
    # Check if instance already exists
    check_cmd = f"gcloud sql instances describe {INSTANCE_NAME} --project={PROJECT_ID}"
    result = run_command(check_cmd, check=False)
    
    if result.returncode == 0:
        print(f"Instance '{INSTANCE_NAME}' already exists.")
        return
    
    # Create new PostgreSQL instance with public IP (simpler for initial setup)
    create_cmd = f"""gcloud sql instances create {INSTANCE_NAME} \
        --project={PROJECT_ID} \
        --database-version=POSTGRES_15 \
        --tier={TIER} \
        --region={REGION} \
        --root-password={ROOT_PASSWORD} \
        --database-flags=cloudsql.iam_authentication=on \
        --authorized-networks=0.0.0.0/0"""
    
    run_command(create_cmd)
    print("Cloud SQL PostgreSQL instance created successfully!")

def create_database():
    """Create database"""
    print(f"\n2. Creating database '{DATABASE_NAME}'...")
    
    cmd = f"""gcloud sql databases create {DATABASE_NAME} \
        --instance={INSTANCE_NAME} \
        --project={PROJECT_ID}"""
    
    result = run_command(cmd, check=False)
    if result.returncode != 0 and "already exists" not in result.stderr:
        print(f"Error creating database: {result.stderr}")
        sys.exit(1)
    
    print("Database created successfully!")

def get_connection_info():
    """Get connection information"""
    print("\n3. Getting connection information...")
    
    # Get instance connection name
    cmd = f"gcloud sql instances describe {INSTANCE_NAME} --project={PROJECT_ID} --format='value(connectionName)'"
    result = run_command(cmd)
    connection_name = result.stdout.strip()
    
    # Get instance IP address
    ip_cmd = f"gcloud sql instances describe {INSTANCE_NAME} --project={PROJECT_ID} --format='value(ipAddresses[0].ipAddress)'"
    ip_result = run_command(ip_cmd)
    ip_address = ip_result.stdout.strip()
    
    print(f"\nConnection Information:")
    print(f"  Instance: {INSTANCE_NAME}")
    print(f"  Database: {DATABASE_NAME}")
    print(f"  Connection Name: {connection_name}")
    print(f"  Public IP: {ip_address}")
    print(f"  Root Password: {ROOT_PASSWORD}")
    print(f"\nTo connect locally:")
    print(f"  Option 1 - Direct connection:")
    print(f"    psql -h {ip_address} -U postgres -d {DATABASE_NAME}")
    print(f"  Option 2 - Cloud SQL Proxy (more secure):")
    print(f"    cloud_sql_proxy -instances={connection_name}=tcp:5432")
    print(f"    psql -h 127.0.0.1 -U postgres -d {DATABASE_NAME}")
    
    return connection_name, ip_address

def create_sql_schema():
    """Create SQL schema file"""
    print("\n4. Creating SQL schema...")
    
    schema = """-- PrepSense Cloud SQL PostgreSQL Schema
-- Optimized for transactional operations with PostgreSQL features

-- Create database (if not exists)
-- CREATE DATABASE prepsense;

-- Connect to the database
-- \c prepsense;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    password_hash VARCHAR(255),
    role VARCHAR(20) DEFAULT 'user' CHECK (role IN ('admin', 'user')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for email and username lookups
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);

-- Pantries table
CREATE TABLE IF NOT EXISTS pantries (
    pantry_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    pantry_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_pantries_user_id ON pantries(user_id);

-- Pantry items table (optimized for frequent updates)
CREATE TABLE IF NOT EXISTS pantry_items (
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
    -- PostgreSQL JSONB for flexible attributes
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Indexes for pantry items
CREATE INDEX IF NOT EXISTS idx_pantry_items_pantry_id ON pantry_items(pantry_id);
CREATE INDEX IF NOT EXISTS idx_pantry_items_expiration ON pantry_items(expiration_date);
CREATE INDEX IF NOT EXISTS idx_pantry_items_status ON pantry_items(status);
CREATE INDEX IF NOT EXISTS idx_pantry_items_category ON pantry_items(category);
CREATE INDEX IF NOT EXISTS idx_pantry_items_metadata ON pantry_items USING GIN(metadata);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    household_size INTEGER DEFAULT 1,
    preferences JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dietary preferences (using PostgreSQL arrays)
CREATE TABLE IF NOT EXISTS user_dietary_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    preference VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, preference)
);

-- Allergens
CREATE TABLE IF NOT EXISTS user_allergens (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    allergen VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, allergen)
);

-- Cuisine preferences
CREATE TABLE IF NOT EXISTS user_cuisine_preferences (
    user_id INTEGER NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    cuisine VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, cuisine)
);

-- Recipes table with JSONB for flexible recipe data
CREATE TABLE IF NOT EXISTS recipes (
    recipe_id SERIAL PRIMARY KEY,
    recipe_name VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100),
    prep_time INTEGER,
    cook_time INTEGER,
    servings INTEGER,
    difficulty VARCHAR(20) DEFAULT 'medium' CHECK (difficulty IN ('easy', 'medium', 'hard')),
    recipe_data JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recipes_cuisine ON recipes(cuisine_type);
CREATE INDEX IF NOT EXISTS idx_recipes_data ON recipes USING GIN(recipe_data);

-- Recipe ingredients
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id INTEGER NOT NULL REFERENCES recipes(recipe_id) ON DELETE CASCADE,
    ingredient_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2),
    unit VARCHAR(50),
    is_optional BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (recipe_id, ingredient_name)
);

-- User saved recipes
CREATE TABLE IF NOT EXISTS user_recipes (
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
);

CREATE INDEX IF NOT EXISTS idx_user_recipes_user_rating ON user_recipes(user_id, rating);
CREATE INDEX IF NOT EXISTS idx_user_recipes_user_favorite ON user_recipes(user_id, is_favorite);

-- Create update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to tables with updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_pantry_items_updated_at BEFORE UPDATE ON pantry_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_recipes_updated_at BEFORE UPDATE ON user_recipes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create default demo user
INSERT INTO users (user_id, username, email, first_name, last_name, role)
VALUES (111, 'demo_user', 'demo@prepsense.com', 'Demo', 'User', 'user')
ON CONFLICT (user_id) DO NOTHING;

-- Create default pantry for demo user
INSERT INTO pantries (user_id, pantry_name)
SELECT 111, 'My Pantry'
WHERE NOT EXISTS (
    SELECT 1 FROM pantries WHERE user_id = 111
);

-- Create view for user pantry items (similar to BigQuery view)
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

-- Grant permissions for IAM users (when using IAM authentication)
-- This will be done after creating IAM database users
"""
    
    schema_file = Path("schema_postgres.sql")
    schema_file.write_text(schema)
    print(f"Schema file created: {schema_file}")
    
    return schema_file

def setup_iam_user(email):
    """Set up IAM database user"""
    print(f"\n5. Setting up IAM user for {email}...")
    
    # Create Cloud SQL user for IAM authentication
    cmd = f"""gcloud sql users create {email} \
        --instance={INSTANCE_NAME} \
        --type=CLOUD_IAM_USER \
        --project={PROJECT_ID}"""
    
    result = run_command(cmd, check=False)
    if result.returncode == 0:
        print(f"IAM user {email} created successfully!")
    elif "already exists" in result.stderr:
        print(f"IAM user {email} already exists.")
    else:
        print(f"Note: Could not create IAM user: {result.stderr}")

def main():
    print("=== PrepSense Cloud SQL PostgreSQL Setup ===")
    
    # Check prerequisites
    print("Checking prerequisites...")
    result = run_command("which gcloud", check=False)
    if result.returncode != 0:
        print("Error: gcloud CLI not found. Please install Google Cloud SDK.")
        sys.exit(1)
    
    # Set project
    run_command(f"gcloud config set project {PROJECT_ID}")
    
    # Enable APIs
    enable_required_apis()
    
    # Create instance
    create_instance()
    
    # Create database
    create_database()
    
    # Get connection info
    connection_name, ip_address = get_connection_info()
    
    # Create schema
    schema_file = create_sql_schema()
    
    # Try to get current user email for IAM setup
    user_email_cmd = "gcloud config get-value account"
    user_email_result = run_command(user_email_cmd, check=False)
    if user_email_result.returncode == 0:
        user_email = user_email_result.stdout.strip()
        if user_email:
            setup_iam_user(user_email)
    
    print("\n=== Setup Complete! ===")
    print("\nNext Steps:")
    print("1. Install Cloud SQL Proxy (recommended for production):")
    print("   curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64")
    print("   chmod +x cloud_sql_proxy")
    print("\n2. Install psql client if needed:")
    print("   brew install postgresql")
    print("\n3. Import the schema:")
    print(f"   PGPASSWORD={ROOT_PASSWORD} psql -h {ip_address} -U postgres -d {DATABASE_NAME} < {schema_file}")
    print("\n4. Update your .env file with:")
    print(f"   # PostgreSQL connection")
    print(f"   DB_TYPE=postgres")
    print(f"   POSTGRES_HOST={ip_address}")
    print(f"   POSTGRES_PORT=5432")
    print(f"   POSTGRES_DATABASE={DATABASE_NAME}")
    print(f"   POSTGRES_USER=postgres")
    print(f"   POSTGRES_PASSWORD={ROOT_PASSWORD}")
    print(f"   CLOUD_SQL_CONNECTION_NAME={connection_name}")
    print(f"\n   # Or for Cloud SQL Proxy (more secure):")
    print(f"   # POSTGRES_HOST=127.0.0.1")
    print("\n5. For IAM authentication (team members):")
    print("   gcloud sql users create [USER_EMAIL] --instance={} --type=CLOUD_IAM_USER".format(INSTANCE_NAME))
    print("\n6. To connect with IAM auth:")
    print("   gcloud sql connect {} --user=[USER_EMAIL] --database={}".format(INSTANCE_NAME, DATABASE_NAME))

if __name__ == "__main__":
    main()