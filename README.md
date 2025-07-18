# PrepSense 🥗  

AI-powered smart pantry management system - University of Chicago Capstone Project 

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- PostgreSQL database
- iOS Simulator (Mac) or Expo Go app (mobile) 

### Setup

1. **Clone and Setup**
   ```bash
   git clone https://github.com/your-org/PrepSense.git
   cd PrepSense
   python3 setup.py  # Select option 1 for complete setup
   ```

2. **Configure Environment**
   ```bash
   cp .env.template .env
   # Edit .env with your API keys and database credentials
   ```

3. **Run the App**
   ```bash
   python run_app.py  # Starts both backend and iOS app
   ```

## 📱 What PrepSense Does

- **Track Pantry Items**: Add items via barcode scan or image recognition
- **Monitor Expiration**: Get alerts before food expires
- **Recipe Suggestions**: AI-powered recipes based on what you have
- **Smart Shopping Lists**: Auto-generate lists based on recipes and inventory
- **Dietary Management**: Track preferences, allergens, and nutrition

## 🏗️ Project Structure

```
PrepSense/
├── backend_gateway/     # FastAPI backend
│   ├── app.py          # Main application
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   └── scripts/        # Database setup & utilities
├── ios-app/            # React Native app
│   ├── app/           # Screen components
│   ├── services/      # API integration
│   └── components/    # Reusable UI components
├── docs/              # Project documentation
├── tests/             # Test suites
├── run_app.py         # Main launcher script
├── setup.py           # Initial setup script
├── requirements.txt   # Python dependencies
└── .env.template      # Environment template
```

## 🛠️ Common Commands

```bash
# Development
python run_app.py                    # Start everything
python run_app.py --backend          # Backend only
python run_app.py --ios              # iOS app only

# Testing
python run_app.py --test-sub         # Run ingredient subtraction tests
python run_app.py --reset-data       # Reset demo data

# Cleanup
python cleanup.py                    # Stop all processes
```

## 🔧 Key Features

### Backend (Port 8000)
- RESTful API with automatic docs at `/docs`
- PostgreSQL database with connection pooling
- AI integration (OpenAI Vision, CrewAI)
- Real-time recipe generation
- Smart ingredient matching and unit conversion

### iOS App (Port 8081)
- Barcode scanning
- Image recognition for receipts
- Real-time pantry updates
- Recipe browsing with filters
- Shopping list management

## 🧪 Testing

Run the automated test suite:
```bash
python run_app.py --test-sub
```

This tests:
- Ingredient quantity subtraction
- Unit conversions (cups → ml, g → lb)
- Smart ingredient matching
- Error handling

See [`tests/ingredient-subtraction/`](./tests/ingredient-subtraction/) for details.

## 📊 Database

PostgreSQL database with main tables:
- `users` - User accounts
- `pantry_items` - Inventory tracking
- `user_recipes` - Saved recipes
- `shopping_lists` - Shopping items

## 🆘 Troubleshooting

**Port already in use?**
```bash
python cleanup.py
```

**Database connection issues?**
- Check PostgreSQL is running
- Verify credentials in `.env`
- Run `python backend_gateway/scripts/setup_demo_data.py` for test data

**iOS app can't connect?**
- Backend runs on `http://localhost:8000`
- Check firewall settings
- Verify both services are running

## 📚 Documentation

- [Architecture Guide](./ios-app/docs/MODULAR_ARCHITECTURE.md)
- [API Documentation](http://localhost:8000/docs) (when running)
- [Test Documentation](./tests/ingredient-subtraction/README.md)
- [Demo & Testing Guide](./docs/DEMO_TEST_GUIDE.md)
- [Recipe Edge Cases](./docs/RECIPE_COMPLETION_EDGE_CASES.md)
- [Stats Screen Design](./docs/STATS_SCREEN_NOTES.md)
- [Migration Guides](./docs/MIGRATE_TO_ADC.md)

## 👥 Team

University of Chicago Capstone Project Team

- Daniel Kim
- Bonny Matthews
- Prahalad Ravi
- Akash Sannidhanam
