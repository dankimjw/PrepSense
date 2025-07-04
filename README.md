# PrepSense 🥗
AI-powered smart pantry management system - Capstone project for University of Chicago

## 🚀 Project Overview

PrepSense is an intelligent pantry management application that helps users:
- Track food inventory with AI-powered image recognition
- Monitor expiration dates to reduce food waste
- Get personalized recipe suggestions based on available ingredients
- Manage dietary preferences and allergens
- Generate shopping lists automatically

## 📚 Getting Started Documentation

⭐ For detailed setup instructions and comprehensive guides, please visit our **[Getting Started Documentation](./docs/README.md)**.

### Quick Links:
- **[Prerequisites & Tools Installation](./docs/getting-started/01-prerequisites.md)** - What you need before starting
- **[Step-by-Step Setup Guide](./docs/getting-started/02-repository-setup.md)** - Clone and configure the project
- **[Troubleshooting Guide](./docs/getting-started/06-troubleshooting.md)** - Common issues and solutions
- **[Helpful Resources](./docs/getting-started/07-resources.md)** - Learning materials and references
- **[Modular Architecture Guide](./ios-app/docs/MODULAR_ARCHITECTURE.md)** - Team collaboration guidelines

## 🏗️ Project Architecture

### Backend Gateway (`/backend_gateway`)
```
backend_gateway/
├── app.py                    # Main FastAPI application entry point
├── routers/                  # API route handlers
│   ├── auth.py              # Authentication endpoints
│   ├── bigquery_router.py   # BigQuery integration routes
│   ├── chat_router.py       # AI chat functionality
│   ├── images_router.py     # Image upload and processing
│   ├── pantry_router.py     # Pantry CRUD operations
│   ├── recipes_router.py    # Recipe generation endpoints
│   └── users.py             # User management
├── services/                 # Core business logic
│   ├── bigquery_service.py  # BigQuery database operations (with schema docs)
│   ├── crew_ai_service.py   # AI agent orchestration
│   ├── pantry_service.py    # Pantry management logic
│   ├── recipe_service.py    # Recipe generation service
│   ├── spoonacular_service.py # Spoonacular API integration
│   ├── user_service.py      # User management service
│   └── vision_service.py    # OpenAI Vision API integration
├── models/                   # Data models
│   └── user.py              # User model definitions
├── core/                     # Core utilities
│   ├── config.py            # Configuration management
│   └── security.py          # Security and authentication
├── database.py              # Database configuration
├── pubsub.py               # Pub/Sub integration
└── requirements.txt         # Python dependencies
```

### iOS Application (`/ios-app`)
```
ios-app/
├── app/                     # Main application screens
│   ├── (tabs)/             # Tab-based navigation screens
│   │   ├── index.tsx       # Home screen (pantry items)
│   │   ├── stats.tsx       # Statistics dashboard
│   │   ├── recipes.tsx     # Recipe suggestions
│   │   ├── admin.tsx       # Admin panel with BigQuery access
│   │   └── profile.tsx     # User profile
│   ├── bigquery-tester.tsx # BigQuery testing interface
│   ├── components/         # Screen-specific components
│   └── utils/              # Utility functions
├── components/              # Shared components
│   ├── home/               # Home screen components
│   │   ├── QuickActions.tsx    # Quick action buttons
│   │   ├── PantryItem.tsx      # Item display component
│   │   ├── PantryItemsList.tsx # Items list container
│   │   └── TipCard.tsx         # Storage tips
│   ├── CustomHeader.tsx    # Header with database access
│   ├── SearchBar.tsx       # Search functionality
│   └── FilterModal.tsx     # Filter and sort modal
├── hooks/                   # Custom React hooks
│   └── useItemsWithFilters.ts # Items filtering logic
├── context/                 # Global state management
│   ├── ItemsContext.tsx    # Pantry items state
│   └── AuthContext.tsx     # Authentication state
├── services/               # API integration
│   └── api.ts             # Backend API client
├── types/                  # TypeScript definitions
│   └── index.ts           # Shared type interfaces
└── utils/                  # Helper functions
    ├── itemHelpers.ts     # Item formatting utilities
    └── encoding.ts        # Navigation encoding
```

### Root Project Files
```
PrepSense/
├── run_app.py              # Unified launcher for backend + iOS
├── cleanup.py              # Python cleanup script
├── cleanup.sh              # Shell cleanup script
├── setup.py                # Interactive setup script
├── .env                    # Environment configuration
├── .env.template           # Environment template
└── config/                 # Configuration files
    ├── openai_key.txt      # OpenAI API key
    └── *.json              # Google Cloud credentials
```


## 🛠️ Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Google BigQuery** - Cloud data warehouse
- **OpenAI Vision API** - Image recognition
- **CrewAI** - AI agent orchestration
- **Python 3.8+** - Backend language

### Frontend (iOS)
- **React Native** - Cross-platform mobile framework
- **Expo** - React Native development platform
- **TypeScript** - Type-safe JavaScript
- **React Navigation** - Navigation library
- **Context API** - State management

### AI/ML
- **OpenAI GPT-4** - Natural language processing
- **OpenAI Vision** - Food item recognition
- **CrewAI Agents** - Recipe generation and recommendations

## 🔧 Prerequisites

Before you begin, ensure you have the following installed:
- **Git** - Version control
- **Python 3.8+** - Backend runtime
- **Node.js** (LTS version) and npm - Frontend runtime
- **Expo CLI** (optional) - React Native development (`npm install -g expo-cli`)
- **iOS Simulator** (Mac only) or **Expo Go** app on your device

## 🚀 Quick Start

### 🎯 Interactive Setup (Recommended)

We provide an interactive Python setup script with menu options:

```bash
python3 setup.py
```

**Menu Options:**
1. **Initial Setup** - Install dependencies, create directories, set up environment
2. **Setup API Keys** - Configure OpenAI and Google Cloud credentials interactively
3. **Exit**

**Option 1 - Initial Setup:**
- ✅ Check all prerequisites (Python 3.8+, Node.js, npm, Git)
- ✅ Create virtual environment and install Python dependencies
- ✅ Install npm packages for iOS app
- ✅ Create required directories (`config/`, `logs/`, `data/`)
- ✅ Set up `.env` file from template
- ✅ Create `config/openai_key.txt` placeholder

**Option 2 - Setup API Keys:**
- ✅ Interactive OpenAI API key configuration with validation
- ✅ Smart Google Cloud credentials detection in `config/` folder
- ✅ Auto-update `.env` with correct credential paths
- ✅ Handle multiple credential files with user selection

### 🏃 Running the Application

#### Unified Launcher (Recommended)

We provide a unified launcher that starts both backend and iOS app with synchronized configuration:

```bash
# Start both backend and iOS app (default)
python3 run_app.py

# Or use command line options:
python3 run_app.py --backend              # Backend only
python3 run_app.py --ios                 # iOS app only
python3 run_app.py --port 8002           # Custom backend port
python3 run_app.py --host 0.0.0.0        # Custom backend host
python3 run_app.py --ios-port 8083       # Custom iOS port
python3 run_app.py --help                # Show all options
```

**Launcher Features:**
- 🔄 Automatic IP synchronization between backend and iOS app
- 🧹 Process cleanup before starting (prevents port conflicts)
- 📱 Auto-launches iOS simulator (press 'i' when prompted)
- 🛑 Graceful shutdown with Ctrl+C
- 🔧 Environment variable support (LAUNCH_MODE, HOST, PORT, etc.)

### 🧹 Cleanup Scripts

If you encounter port conflicts or need to stop all PrepSense processes:

```bash
# Python cleanup script (recommended)
python3 cleanup.py

# Or shell script
./cleanup.sh
```

These scripts will:
- Kill processes on ports: 8001 (backend), 8082/8083 (iOS), 19000-19002, 19006 (Expo)
- Stop processes by name: expo, metro, start.py, run_app.py, uvicorn, fastapi
- Verify all processes are stopped



## 💾 Database Schema

The application uses Google BigQuery with the dataset `adsp-34002-on02-prep-sense.Inventory`.

### Core Tables

#### 🏠 `pantry` - User pantries
| Column | Type | Description |
|--------|------|-------------|
| pantry_id | INTEGER | Unique pantry identifier |
| user_id | INTEGER | Associated user ID |
| pantry_name | STRING | Name of the pantry |
| created_at | DATETIME | Creation timestamp |

#### 🥫 `pantry_items` - Inventory tracking
| Column | Type | Description |
|--------|------|-------------|
| pantry_item_id | INTEGER | Unique item identifier |
| pantry_id | INTEGER | Associated pantry ID |
| quantity | FLOAT | Item quantity |
| unit_of_measurement | STRING | Unit (kg, lb, count, etc.) |
| expiration_date | DATE | Expiration date |
| unit_price | FLOAT | Price per unit |
| total_price | FLOAT | Total item cost |
| created_at | DATETIME | Creation timestamp |
| used_quantity | INTEGER | Amount used |
| status | STRING | Item status |

#### 📦 `products` - Product information
| Column | Type | Description |
|--------|------|-------------|
| product_id | INTEGER | Unique product identifier |
| pantry_item_id | INTEGER | Associated pantry item |
| product_name | STRING | Product name |
| brand_name | STRING | Brand name |
| category | STRING | Product category |
| upc_code | STRING | Universal Product Code |
| created_at | DATETIME | Creation timestamp |

#### 🍳 `recipies` - Recipe database
| Column | Type | Description |
|--------|------|-------------|
| recipe_id | INTEGER | Unique recipe identifier |
| product_id | INTEGER | Required product |
| recipe_name | STRING | Recipe name |
| quantity_needed | FLOAT | Required quantity |
| unit_of_measurement | STRING | Measurement unit |
| instructions | STRING | Cooking instructions |
| created_at | DATETIME | Creation timestamp |

#### 👤 `user` - User accounts
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Unique user identifier |
| user_name | STRING | Username |
| first_name | STRING | First name |
| last_name | STRING | Last name |
| email | STRING | Email address |
| password_hash | STRING | Encrypted password |
| role | STRING | User role |
| api_key_enc | BYTES | Encrypted API key |
| created_at | DATETIME | Creation timestamp |

#### ⚙️ `user_preference` - User preferences
| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Associated user ID |
| household_size | INTEGER | Number of people |
| dietary_preference | STRING[] | Dietary restrictions (REPEATED) |
| allergens | STRING[] | Food allergies (REPEATED) |
| cuisine_preference | STRING[] | Preferred cuisines (REPEATED) |
| created_at | DATETIME | Creation timestamp |

## 📋 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/PrepSense.git
cd PrepSense
```

### 2. Interactive Setup (Recommended)

Run the interactive Python setup script:

```bash
python3 setup.py
```

1. Select **option 1** for initial setup (dependencies, directories, environment)
2. Select **option 2** to configure API keys (OpenAI + Google Cloud auto-detection)

### 3. Manual Setup (Alternative)

If you prefer manual setup or the automated script fails:

#### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.template .env

# Edit .env with your API keys
```

#### iOS App Setup

```bash
# Install dependencies
cd ios-app
npm install
cd ..
```

#### Configure Environment Variables

The interactive setup script handles most configuration automatically, but for manual setup:

**1. OpenAI Configuration:**
- Place your API key in `config/openai_key.txt`
- The `.env` file is already configured to read from this file

**2. Google Cloud Configuration (RECOMMENDED - Use ADC):**

**Option A: Application Default Credentials (Recommended for team projects)**
```bash
# One-time setup for each team member
gcloud auth login                          # For CLI access
gcloud auth application-default login       # For application access
gcloud config set project adsp-34002-on02-prep-sense
```
- No JSON key files to share or manage
- Uses OAuth tokens tied to each developer's Google account
- More secure and follows Google's best practices
- Leave `GOOGLE_APPLICATION_CREDENTIALS` commented out in `.env`

**Option B: Service Account Key (Only if ADC doesn't work)**
- Place your service account JSON file in the `config/` directory
- The setup script auto-detects and configures the path in `.env`
- Manual path format: `GOOGLE_APPLICATION_CREDENTIALS=config/your-service-account-key.json`
- ⚠️ Never commit key files to Git!

### 4. Running the Application

```bash
# Unified launcher - starts both backend and iOS app
python3 run_app.py

# Alternative: Start services separately
python3 run_app.py --backend    # Backend only on port 8001
python3 run_app.py --ios        # iOS app only on port 8082
```

#### Access Points
- **API Documentation**: `http://localhost:8001/docs`
- **Backend Health Check**: `http://localhost:8001/health`
- **iOS Simulator**: Automatically opens on Mac (press 'i' when prompted)
- **Physical Device**: Scan QR code with Expo Go app
- **Web Browser**: Press 'w' in the terminal

### 4. Testing Tips

#### Using iOS Simulator
1. **Add Test Images**: Drag image files onto the simulator to add them to Photos
2. **Test Upload**: Use "Upload Image" in the app to test AI recognition
3. **Manual Entry**: Use "Add Item" for quick testing without images

#### API Testing
- FastAPI docs: `http://localhost:8001/docs`
- Interactive API testing: `http://localhost:8001/redoc`

## 🤝 Collaboration Guidelines

### 🌳 Git Workflow

#### Branch Strategy
```
main
├── feature/add-shopping-list
├── feature/recipe-filters
├── fix/expiration-date-bug
└── refactor/modular-components
```

#### Development Process
```bash
# 1. Start from updated main
git checkout main
git pull origin main

# 2. Create feature branch
git checkout -b feature/your-feature

# 3. Make changes and commit
git add .
git commit -m "feat: add ingredient search"

# 4. Push to remote
git push -u origin feature/your-feature

# 5. Create Pull Request on GitHub
```

### 📝 Commit Convention
| Type | Description | Example |
|------|-------------|---------|
| `feat:` | New feature | `feat: add recipe sharing` |
| `fix:` | Bug fix | `fix: correct expiration calculation` |
| `docs:` | Documentation | `docs: update API endpoints` |
| `style:` | Formatting | `style: fix indentation` |
| `refactor:` | Code restructuring | `refactor: modularize home screen` |
| `test:` | Add tests | `test: add pantry service tests` |
| `chore:` | Maintenance | `chore: update dependencies` |

### 🏗️ Modular Architecture

The codebase follows a modular architecture for better team collaboration:

- **Components are isolated** - Work on different features without conflicts
- **Clear interfaces** - TypeScript ensures type safety
- **Shared utilities** - Reusable functions in `utils/`
- **Custom hooks** - Business logic separated from UI

See the [Modular Architecture Guide](./ios-app/docs/MODULAR_ARCHITECTURE.md) for details.

### 👥 Team Guidelines

#### Code Review
- All PRs require at least one review
- Run tests before requesting review
- Address feedback promptly
- Keep PRs focused and small

#### Development Setup
1. **Use virtual environment** for Python
2. **Run linters** before committing
3. **Test on iOS simulator** and devices
4. **Update documentation** for new features

#### Security Best Practices
- Never commit `.env` files
- Use environment variables for secrets
- Rotate API keys regularly
- Follow OWASP guidelines

## 🐛 Troubleshooting

### Common Issues

#### Backend Won't Start
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Check port availability
lsof -i :8001  # Kill any process using the port
```

#### iOS App Connection Issues
```bash
# The unified launcher handles IP configuration automatically
python3 run_app.py

# Or manually specify host for network access
python3 run_app.py --host 0.0.0.0

# Check network connectivity
# API base URL is auto-configured by launcher
```

#### BigQuery Authentication
```bash
# Credentials should be in config/ directory
# The launcher auto-detects and configures them

# Manual verification
export GOOGLE_APPLICATION_CREDENTIALS="config/your-service-account.json"

# Check BigQuery connectivity
curl http://localhost:8001/api/v1/bigquery/tables

# Note: The app requires real BigQuery credentials
# Development mode with mock data has been removed
```

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Expo Documentation](https://docs.expo.dev/)
- [React Native Docs](https://reactnative.dev/)
- [BigQuery Documentation](https://cloud.google.com/bigquery/docs)
- [OpenAI API Reference](https://platform.openai.com/docs)

## 📄 License

This project is part of the University of Chicago Capstone program.

---

Built with ❤️ by the PrepSense Team

