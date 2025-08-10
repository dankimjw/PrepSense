#!/usr/bin/env python3
"""
Setup script for Cloud SQL instance and database schema for PrepSense
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
PROJECT_ID = "adsp-34002-on02-prep-sense"
INSTANCE_NAME = "prepsense-db"
REGION = "us-central1"
TIER = "db-f1-micro"  # Small instance for development
DATABASE_NAME = "prepsense"

# Get password from environment variable
ROOT_PASSWORD = os.getenv("MYSQL_ROOT_PASSWORD")
if not ROOT_PASSWORD:
    print("Error: MYSQL_ROOT_PASSWORD environment variable is required")
    print("Please set it using: export MYSQL_ROOT_PASSWORD='your-password'")
    sys.exit(1)


def run_command(cmd, check=True):
    """Run a command and return the result"""
    print(f"Running: {cmd}")
    result = subprocess.run(cmd, check=False, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"Error: {result.stderr}")
        sys.exit(1)
    return result


def create_instance():
    """Create Cloud SQL instance"""
    print(f"\n1. Creating Cloud SQL instance '{INSTANCE_NAME}'...")

    # Check if instance already exists
    check_cmd = f"gcloud sql instances describe {INSTANCE_NAME} --project={PROJECT_ID}"
    result = run_command(check_cmd, check=False)

    if result.returncode == 0:
        print(f"Instance '{INSTANCE_NAME}' already exists.")
        return

    # Create new instance with public IP (simpler for initial setup)
    create_cmd = f"""gcloud sql instances create {INSTANCE_NAME} \
        --project={PROJECT_ID} \
        --database-version=MYSQL_8_0 \
        --tier={TIER} \
        --region={REGION} \
        --root-password={ROOT_PASSWORD} \
        --authorized-networks=0.0.0.0/0"""

    run_command(create_cmd)
    print("Cloud SQL instance created successfully!")


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


def enable_required_apis():
    """Enable required APIs for Cloud SQL"""
    print("\n0. Enabling required APIs...")
    apis = ["sqladmin.googleapis.com", "compute.googleapis.com", "servicenetworking.googleapis.com"]

    for api in apis:
        cmd = f"gcloud services enable {api} --project={PROJECT_ID}"
        print(f"Enabling {api}...")
        run_command(cmd)

    print("All required APIs enabled!")


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

    print("\nConnection Information:")
    print(f"  Instance: {INSTANCE_NAME}")
    print(f"  Database: {DATABASE_NAME}")
    print(f"  Connection Name: {connection_name}")
    print(f"  Public IP: {ip_address}")
    print(f"  Root Password: {ROOT_PASSWORD}")
    print("\nTo connect locally:")
    print("  Option 1 - Direct connection:")
    print(f"    mysql -h {ip_address} -u root -p{ROOT_PASSWORD}")
    print("  Option 2 - Cloud SQL Proxy (more secure):")
    print(f"    cloud_sql_proxy -instances={connection_name}=tcp:3306")
    print(f"    mysql -h 127.0.0.1 -u root -p{ROOT_PASSWORD}")

    return connection_name, ip_address


def create_sql_schema():
    """Create SQL schema file"""
    print("\n4. Creating SQL schema...")

    schema = """-- PrepSense Cloud SQL Schema
-- Optimized for transactional operations

CREATE DATABASE IF NOT EXISTS prepsense;
USE prepsense;

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    password_hash VARCHAR(255),
    role ENUM('admin', 'user') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_email (email),
    INDEX idx_username (username)
);

-- Pantries table
CREATE TABLE IF NOT EXISTS pantries (
    pantry_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    pantry_name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
);

-- Pantry items table (optimized for frequent updates)
CREATE TABLE IF NOT EXISTS pantry_items (
    pantry_item_id INT PRIMARY KEY AUTO_INCREMENT,
    pantry_id INT NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    brand_name VARCHAR(255),
    category VARCHAR(100) DEFAULT 'Uncategorized',
    quantity DECIMAL(10, 2) NOT NULL DEFAULT 0,
    unit_of_measurement VARCHAR(50),
    expiration_date DATE,
    unit_price DECIMAL(10, 2),
    total_price DECIMAL(10, 2),
    source ENUM('manual', 'vision_detected', 'receipt_scan') DEFAULT 'manual',
    status ENUM('available', 'consumed', 'expired') DEFAULT 'available',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    consumed_at TIMESTAMP NULL,
    used_quantity DECIMAL(10, 2) DEFAULT 0,
    FOREIGN KEY (pantry_id) REFERENCES pantries(pantry_id) ON DELETE CASCADE,
    INDEX idx_pantry_id (pantry_id),
    INDEX idx_expiration (expiration_date),
    INDEX idx_status (status),
    INDEX idx_category (category)
);

-- User preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL UNIQUE,
    household_size INT DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Dietary preferences (many-to-many)
CREATE TABLE IF NOT EXISTS user_dietary_preferences (
    user_id INT NOT NULL,
    preference VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, preference),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Allergens (many-to-many)
CREATE TABLE IF NOT EXISTS user_allergens (
    user_id INT NOT NULL,
    allergen VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, allergen),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Cuisine preferences (many-to-many)
CREATE TABLE IF NOT EXISTS user_cuisine_preferences (
    user_id INT NOT NULL,
    cuisine VARCHAR(100) NOT NULL,
    PRIMARY KEY (user_id, cuisine),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- Recipes table
CREATE TABLE IF NOT EXISTS recipes (
    recipe_id INT PRIMARY KEY AUTO_INCREMENT,
    recipe_name VARCHAR(255) NOT NULL,
    cuisine_type VARCHAR(100),
    prep_time INT,
    cook_time INT,
    servings INT,
    difficulty ENUM('easy', 'medium', 'hard') DEFAULT 'medium',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_cuisine (cuisine_type)
);

-- Recipe ingredients (many-to-many)
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    recipe_id INT NOT NULL,
    ingredient_name VARCHAR(255) NOT NULL,
    quantity DECIMAL(10, 2),
    unit VARCHAR(50),
    is_optional BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (recipe_id, ingredient_name),
    FOREIGN KEY (recipe_id) REFERENCES recipes(recipe_id) ON DELETE CASCADE
);

-- User saved recipes
CREATE TABLE IF NOT EXISTS user_recipes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    recipe_id INT,
    recipe_title VARCHAR(255) NOT NULL,
    recipe_image TEXT,
    recipe_data JSON,
    rating ENUM('thumbs_up', 'thumbs_down', 'neutral') DEFAULT 'neutral',
    is_favorite BOOLEAN DEFAULT FALSE,
    source VARCHAR(50) DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    INDEX idx_user_rating (user_id, rating),
    INDEX idx_user_favorite (user_id, is_favorite)
);

-- Create default demo user
INSERT INTO users (user_id, username, email, first_name, last_name, role)
VALUES (111, 'demo_user', 'demo@prepsense.com', 'Demo', 'User', 'user')
ON DUPLICATE KEY UPDATE user_id=user_id;

-- Create default pantry for demo user
INSERT INTO pantries (user_id, pantry_name)
SELECT 111, 'My Pantry'
WHERE NOT EXISTS (
    SELECT 1 FROM pantries WHERE user_id = 111
);
"""

    schema_file = Path("schema.sql")
    schema_file.write_text(schema)
    print(f"Schema file created: {schema_file}")

    return schema_file


def main():
    print("=== PrepSense Cloud SQL Setup ===")

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

    print("\n=== Setup Complete! ===")
    print("\nNext Steps:")
    print("1. Install Cloud SQL Proxy (recommended for production):")
    print("   curl -o cloud_sql_proxy https://dl.google.com/cloudsql/cloud_sql_proxy.darwin.amd64")
    print("   chmod +x cloud_sql_proxy")
    print("\n2. Import the schema:")
    print(f"   mysql -h {ip_address} -u root -p$MYSQL_ROOT_PASSWORD < {schema_file}")
    print("\n3. Update your .env file with:")
    print("   # Direct connection (for development)")
    print(f"   MYSQL_HOST={ip_address}")
    print("   MYSQL_PORT=3306")
    print(f"   MYSQL_DATABASE={DATABASE_NAME}")
    print("   MYSQL_USER=root")
    print("   MYSQL_PASSWORD=$MYSQL_ROOT_PASSWORD")
    print(f"   CLOUD_SQL_CONNECTION_NAME={connection_name}")
    print("\n   # Or for Cloud SQL Proxy (more secure):")
    print("   # MYSQL_HOST=127.0.0.1")


if __name__ == "__main__":
    main()
