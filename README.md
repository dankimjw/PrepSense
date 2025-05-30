# PrepSense
Capstone project for University of Chicago 

## 📚 Getting Started Documentation

For detailed setup instructions and comprehensive guides, please visit our **[Getting Started Documentation](./docs/README.md)**.

### Quick Links:
- **[Prerequisites & Tools Installation](./docs/getting-started/01-prerequisites.md)** - What you need before starting
- **[Step-by-Step Setup Guide](./docs/getting-started/02-repository-setup.md)** - Clone and configure the project
- **[Troubleshooting Guide](./docs/getting-started/06-troubleshooting.md)** - Common issues and solutions
- **[Helpful Resources](./docs/getting-started/07-resources.md)** - Learning materials and references
```
/backend-gateway
    ├── app.py                # Main FastAPI app (entry point)
    ├── routers/              # Directory for route handlers
    │   ├── images.py         # Routes for image upload and processing
    │   ├── pantry.py         # Routes for pantry CRUD operations
    │   ├── recipes.py        # Routes for recipe suggestions
    ├── services/             # Directory for core business logic
    │   ├── vision_service.py # Logic for calling OpenAI Vision API or CV microservice
    │   ├── pantry_service.py # Logic for pantry database operations
    │   ├── recipe_service.py # Logic for recipe generation
    ├── models.py             # Pydantic models for request/response validation
    ├── database.py           # Database connection and setup
    ├── pubsub.py             # Pub/Sub integration (if asynchronous processing is used)
    ├── requirements.txt      # Python dependencies
    ├── .env                  # Environment variables (e.g., VISION_URL, DB credentials)
```


## Prerequisites

Before you begin, ensure you have the following installed:
- Git
- Python 3.8+
- Node.js (LTS version recommended) and npm (comes with Node.js)
- Expo CLI (you can install it globally via `npm install -g expo-cli` or use `npx` for commands)

## Quick Start

To start the backend or iOS app, use the following commands from the project root:

```bash
# Start the FastAPI backend server (runs on port 8001)
python run_server.py

# Start the iOS app
python run_ios.py
```

## Database Schema

The application uses Google BigQuery with the dataset `adsp-34002-on02-prep-sense.Inventory`. Below is the detailed schema for all tables:

### 1. `pantry`
- `pantry_id` (INTEGER, NULLABLE)
- `user_id` (INTEGER, NULLABLE)
- `pantry_name` (STRING, NULLABLE)
- `created_at` (DATETIME, NULLABLE)

### 2. `pantry_items`
- `pantry_item_id` (INTEGER, NULLABLE)
- `pantry_id` (INTEGER, NULLABLE)
- `quantity` (FLOAT, NULLABLE)
- `unit_of_measurement` (STRING, NULLABLE)
- `expiration_date` (DATE, NULLABLE)
- `unit_price` (FLOAT, NULLABLE)
- `total_price` (FLOAT, NULLABLE)
- `created_at` (DATETIME, NULLABLE)
- `used_quantity` (INTEGER, NULLABLE)
- `status` (STRING, NULLABLE)

### 3. `products`
- `product_id` (INTEGER, NULLABLE)
- `pantry_item_id` (INTEGER, NULLABLE)
- `product_name` (STRING, NULLABLE)
- `brand_name` (STRING, NULLABLE)
- `category` (STRING, NULLABLE)
- `upc_code` (STRING, NULLABLE)
- `created_at` (DATETIME, NULLABLE)

### 4. `recipies`
- `recipe_id` (INTEGER, NULLABLE)
- `product_id` (INTEGER, NULLABLE)
- `recipe_name` (STRING, NULLABLE)
- `quantity_needed` (FLOAT, NULLABLE)
- `unit_of_measurement` (STRING, NULLABLE)
- `instructions` (STRING, NULLABLE)
- `created_at` (DATETIME, NULLABLE)

### 5. `user`
- `user_id` (INTEGER, NULLABLE)
- `user_name` (STRING, NULLABLE)
- `first_name` (STRING, NULLABLE)
- `last_name` (STRING, NULLABLE)
- `email` (STRING, NULLABLE)
- `password_hash` (STRING, NULLABLE)
- `role` (STRING, NULLABLE)
- `api_key_enc` (BYTES, NULLABLE)
- `created_at` (DATETIME, NULLABLE)

### 6. `user_preference`
- `user_id` (INTEGER, NULLABLE)
- `household_size` (INTEGER, NULLABLE)
- `dietary_preference` (STRING, REPEATED)
- `allergens` (STRING, REPEATED)
- `cuisine_preference` (STRING, REPEATED)
- `created_at` (DATETIME, NULLABLE)

### Key Observations:
1. The `pantry_items` table tracks inventory with details like quantity, expiration, and usage.
2. The `products` table contains product information linked to pantry items.
3. The `recipies` table stores recipe information, linked to products.
4. User management is handled through the `user` and `user_preference` tables.
5. The `user_preference` table uses REPEATED fields for multiple selections like dietary preferences and allergens.

## Getting Started

Follow these steps to set up the project environment.

### 1. Backend Setup (`backend-gateway`)

These steps will guide you through setting up the backend service. The Python virtual environment (`venv`) will be created and activated from the project root (`PrepSense`).

#### a. Create and activate a virtual environment (from the `PrepSense` root directory):
It's recommended to use a virtual environment to manage Python dependencies.
```bash
python3 -m venv venv
source venv/bin/activate
```

#### b. Install dependencies:
```bash
pip install -r requirements.txt
```

#### c. Set up environment variables:
- Create a `.env` file in the `backend-gateway` directory.
- Add the required variables (e.g., `VISION_URL`, `OPENAI_API_KEY`):
```bash
VISION_URL=http://localhost:8001/detect
OPENAI_API_KEY=your_openai_api_key
```

#### d. Run the FastAPI app:
```bash
# Bind to all interfaces so mobile devices can reach the server
SERVER_HOST=0.0.0.0 python run_server.py
```

The backend will be available on your machine's IP address (e.g., `http://192.168.1.X:8001`).

`run_ios.py` will automatically detect this IP and configure the Expo app accordingly.

### 2. iOS App Setup

#### a. Install dependencies:
```bash
cd ios-app
npm install
```

#### b. Start the app:
```bash
# From the project root
python run_ios.py
```

The app will start and provide a QR code that you can scan with the Expo Go app on your iOS device.

### Testing image upload in the iOS simulator

When running the app in the iOS simulator you can quickly add photos without
using a real device:

1. Drag any image file from your Mac onto the simulator window. It will be
   imported into the Photos app inside the simulator.
2. In the PrepSense app tap **Upload Image** and choose the photo you just added.
3. Tap **Confirm** on the next screen to send the image to the backend (and then
   on to OpenAI).

This mirrors the flow on a physical device while keeping development entirely on
your desktop.

## Collaboration Guidelines

### Branch Management
1. **Main Branch (`main`)**
   - This is the production-ready branch
   - Never commit directly to `main`
   - All changes must come through pull requests

2. **Feature Branches**
   - Create a new branch for each feature/fix
   - Branch naming convention: `feature/feature-name` or `fix/issue-name`
   - Example: `feature/loading-screen`, `fix/auth-bug`

3. **Development Workflow**
   ```bash
   # 1. Always start from an up-to-date main branch
   git checkout main
   git pull origin main

   # 2. Create and switch to your feature branch
   git checkout -b feature/your-feature-name

   # 3. Make your changes and commit them
   git add .
   git commit -m "feat: your descriptive commit message"

   # 4. Push your branch to remote
   git push -u origin feature/your-feature-name

   # 5. Create a pull request on GitHub
   # 6. After review and approval, merge into main
   ```

### Commit Message Guidelines
- Use clear, descriptive messages
- Start with a type: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Example: `feat: add loading screen with facts`

### Code Review Process
1. Create a pull request for your changes
2. Request review from at least one team member
3. Address any feedback or requested changes
4. Once approved, merge into main

### Environment Setup
1. **Virtual Environment**
   - Always use the virtual environment
   - Activate it using: `source venv/bin/activate`
   - Keep `requirements.txt` updated
   - Document any new dependencies

2. **Backend Setup**
   - Navigate to project root directory
   - Run: `python run_server.py`
   - Server will be available at `http://127.0.0.1:8001`

3. **iOS App Setup**
   - Navigate to project root directory
   - Run: `python run_ios.py`
   - Use Expo Go app to test on your device

4. **Security**
   - Never commit sensitive data or API keys
   - Keep `.env` files local and in `.gitignore`

### Best Practices
1. **Code Organization**
   - Keep related files together
   - Follow the existing project structure
   - Document new components or functions

2. **Testing**
   - Write tests for new features
   - Ensure all tests pass before merging

3. **Documentation**
   - Update README for significant changes
   - Document API changes
   - Add comments for complex logic

4. **Regular Updates**
   - Pull from main regularly to stay up to date
   - Resolve conflicts early
   - Keep your feature branch current

### Getting Help
- Check existing documentation first
- Ask in team chat for quick questions
- Schedule a meeting for complex issues
- Document solutions for future reference

