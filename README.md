# PrepSense 🥗
AI-powered smart pantry management system - Capstone project for University of Chicago

## 🚀 Project Overview

PrepSense is an intelligent pantry management application that helps users:
- Track food inventory with AI-powered image recognition
- Monitor expiration dates to reduce food waste
- Get personalized recipe suggestions based on available ingredients
- Manage dietary preferences and allergens
- Generate shopping lists automatically

## 🏗️ Architecture Overview

### Backend
- **FastAPI** for RESTful API endpoints
- **Google BigQuery** for data storage and analytics
- **Google Cloud Service Account** for secure authentication
- **OpenAI Vision API** for image recognition
- **CrewAI** for AI agent orchestration

### iOS App (React Native)
- Built with **Expo** and **TypeScript**
- **Context API** for state management
- **React Navigation** for routing
- **Expo Router** for file-based routing
- **NativeWind** for styling

## 🛠️ Prerequisites

Before you begin, ensure you have the following installed:

### System Requirements
- Python 3.8 or higher
- Node.js (LTS version)
- npm or yarn package manager
- Git

### Google Cloud Setup
1. **Access Existing Project**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Select the existing project: `adsp-34002-on02-prep-sense`
   - Ensure you have the necessary permissions to access BigQuery and IAM

2. **Verify Required APIs**
   - The following APIs should already be enabled:
     - Google BigQuery API
     - Google Cloud Storage API (if using image storage)
   - If you need to verify, go to "APIs & Services" > "Library" and search for these APIs

3. **Service Account Access**
   - Contact your project administrator to get access to the service account credentials
   - The service account should have the following roles:
     - BigQuery Data Owner
     - BigQuery Job User
   - You'll receive a JSON key file for authentication

### OpenAI Setup
1. **Get API Key**
   - Go to [OpenAI Platform](https://platform.openai.com/)
   - Create an account if needed
   - Navigate to API Keys
   - Create a new secret key

## ⚙️ Environment Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/PrepSense.git
   cd PrepSense
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Set up iOS app dependencies**
   ```bash
   cd ios-app
   npm install
   cd ..
   ```

4. **Create .env file**
   Create a new file named `.env` in the project root with the following content:

   ```env
   # ===================================
   # Application Settings
   # ===================================
   DEBUG=true
   DEVELOPMENT_MODE=false  # Set to true for local development without BigQuery

   # ===================================
   # API Settings
   # ===================================
   API_V1_STR=/api/v1
   SECRET_KEY=your-secret-key-here-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=11520  # 8 days in minutes

   # ===================================
   # Server Settings
   # ===================================
   HOST=0.0.0.0
   PORT=8001
   RELOAD=True

   # ===================================
   # Google Cloud Settings
   # ===================================
   # Path to your service account JSON key file
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account.json
   
   # Your Google Cloud Project ID
   BIGQUERY_PROJECT=your-project-id
   
   # BigQuery dataset name
   BIGQUERY_DATASET=Inventory
   
   # BigQuery location
   BIGQUERY_LOCATION=US

   # ===================================
   # OpenAI Configuration
   # ===================================
   OPENAI_API_KEY=your-openai-api-key

   # ===================================
   # Admin User Configuration
   # ===================================
   ADMIN_EMAIL=admin@example.com
   ADMIN_PASSWORD=admin123  # Change this in production
   ```

5. **Configure CORS (Optional)**
   Uncomment and modify the following in your `.env` if you need CORS:
   ```env
   # ===================================
   # CORS Settings
   # ===================================
   BACKEND_CORS_ORIGINS=http://localhost:8082,http://127.0.0.1:8082,http://0.0.0.0:8082
   ```

## 🚀 Running the Application

### Using the Unified Launcher

PrepSense includes a unified launcher that handles both backend and frontend:

```bash
# Start both backend and iOS app (default)
python run_app.py

# Start backend server only
python run_app.py --backend

# Start iOS app only
python run_app.py --ios

# Custom port configuration
python run_app.py --port 8002 --ios-port 8083

# Show help
python run_app.py --help
```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to Google Cloud service account JSON key | Yes | - |
| `BIGQUERY_PROJECT` | Google Cloud Project ID | Yes | - |
| `BIGQUERY_DATASET` | BigQuery dataset name | Yes | `Inventory` |
| `BIGQUERY_LOCATION` | BigQuery location | Yes | `US` |
| `OPENAI_API_KEY` | OpenAI API key for AI features | Yes | - |
| `DEVELOPMENT_MODE` | Enable development mode (uses mock data) | No | `false` |
| `DEBUG` | Enable debug logging | No | `false` |
| `HOST` | Backend server host | No | `0.0.0.0` |
| `PORT` | Backend server port | No | `8001` |

## 🧹 Cleanup Scripts

Use the provided cleanup scripts when encountering issues:

```bash
# Python version
python cleanup.py

# Or shell script version
./cleanup.sh
```

## 📚 Documentation

For more detailed information, see:
- [API Documentation](http://localhost:8001/docs) (when backend is running)
- [Expo Documentation](https://docs.expo.dev/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Google BigQuery Documentation](https://cloud.google.com/bigquery/docs)

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

## 🗃️ Project Architecture

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
│   ├── bigquery_service.py  # BigQuery database operations
│   ├── crew_ai_service.py   # AI agent orchestration
│   ├── pantry_service.py    # Pantry management logic
│   ├── recipe_service.py    # Recipe generation service
│   ├── user_service.py      # User management service
│   └── vision_service.py    # OpenAI Vision API integration
├── models/                   # Data models
│   └── user.py              # User model definitions
├── core/                     # Core utilities
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
│   │   └── profile.tsx     # User profile
│   ├── components/         # Screen-specific components
│   └── utils/              # Utility functions
├── components/              # Shared components
│   ├── home/               # Home screen components
│   │   ├── QuickActions.tsx    # Quick action buttons
│   │   ├── PantryItem.tsx      # Item display component
│   │   ├── PantryItemsList.tsx # Items list container
│   │   └── TipCard.tsx         # Storage tips
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
- **Expo CLI** - React Native development (`npm install -g expo-cli`)
- **iOS Simulator** (Mac only) or **Expo Go** app on your device

## 🚀 Quick Start

To start the backend or iOS app, use the following commands from the project root:

```bash
# Start the FastAPI backend server (runs on port 8001)
python run_server.py

# Start the iOS app (in a new terminal)
python run_ios.py
```

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

### 2. Backend Setup

#### Create Virtual Environment
```bash
# From the project root directory
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
Create a `.env` file in the `backend-gateway` directory:
```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Server Configuration
VISION_URL=http://localhost:8001/detect
SERVER_HOST=0.0.0.0  # Allows mobile devices to connect

# Google Cloud Configuration
GOOGLE_APPLICATION_CREDENTIALS=path/to/your/credentials.json
```

#### Start the Backend Server
```bash
# From project root
python run_server.py
```
The API will be available at `http://localhost:8001` (or your machine's IP on port 8001).

### 3. iOS App Setup

#### Install Dependencies
```bash
cd ios-app
npm install
cd ..  # Return to project root
```

#### Start the iOS App
```bash
# From project root
python run_ios.py
```

#### Access the App
- **iOS Simulator**: Automatically opens on Mac
- **Physical Device**: Scan the QR code with Expo Go app
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
# Ensure backend is running on all interfaces
SERVER_HOST=0.0.0.0 python run_server.py

# Check firewall settings
# Update API_BASE_URL in constants/Config.ts
```

#### BigQuery Authentication
```bash
# Set credentials path
export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"

# Verify credentials
gcloud auth application-default login
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

