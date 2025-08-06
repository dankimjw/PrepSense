# 📚 PrepSense Documentation

Welcome! This is the public documentation for PrepSense, a smart pantry management application that helps you track inventory, reduce food waste, and discover recipes based on what you have.

## 🚀 Getting Started

New to PrepSense? Start here:

1. **[Prerequisites & Tools](./getting-started/01-prerequisites.md)** - What you need before starting
2. **[Repository Setup](./getting-started/02-repository-setup.md)** - Clone and initial setup
3. **[Backend Setup](./getting-started/03-backend-setup.md)** - Python & FastAPI setup
4. **[Frontend Setup](./getting-started/04-frontend-setup.md)** - Node.js & Expo setup
5. **[Running the App](./getting-started/05-running-app.md)** - Launch everything together

## 📱 What is PrepSense?

PrepSense is a smart pantry management application that helps you:

- **Track your pantry items** with automatic expiration monitoring
- **Get recipe suggestions** based on ingredients you have
- **Reduce food waste** through intelligent usage recommendations
- **Plan your meals** with personalized recipe filtering
- **Scan items** using AI-powered image recognition

## 🏗️ Architecture Overview

The app consists of:

- **Frontend**: React Native Expo app (`ios-app/`)
- **Backend**: Python FastAPI server (`backend_gateway/`)
- **Database**: PostgreSQL hosted on Google Cloud SQL
- **AI Services**: Vision API for image recognition, CrewAI for intelligent recommendations

## 📖 Documentation Sections

### 🛠️ API & Technical Documentation
- **[API Documentation](./api/)** - Backend API endpoints, database schemas, and integration guides
- **[Architecture Documentation](./architecture/)** - System architecture, data flows, and feature specifications

### 🤝 Contributing
- **[Developer Guide](./contributing/DEVELOPER_GUIDE.md)** - Development workflow, code quality, and testing
- **[Contributing Guidelines](./contributing/)** - How to contribute to the project

### 📋 Features & Guides
- **[Feature Documentation](./FEATURE_DOCUMENTATION.md)** - Complete feature overview with usage examples
- **[User Guide v1.0](./Guide_v1.0.md)** - Comprehensive user manual
- **[Changelog](./CHANGELOG.md)** - Technical changes and updates

## 🎯 Quick Links

### For Users
- [Feature Documentation](./FEATURE_DOCUMENTATION.md) - Learn about all features
- [User Guide](./Guide_v1.0.md) - Complete usage guide
- [Troubleshooting](./getting-started/06-troubleshooting.md) - Common issues and solutions

### For Developers
- [API Documentation](./api/) - Backend endpoints and schemas
- [Architecture Overview](./architecture/) - System design and data flows
- [Developer Guide](./contributing/DEVELOPER_GUIDE.md) - Development setup and workflow

### For Contributors
- [Getting Started](./getting-started/) - Setup instructions
- [Contributing Guide](./contributing/) - How to contribute
- [Testing Requirements](./contributing/TESTING_REQUIREMENTS.md) - Testing standards

## 🌟 Key Features

### Smart Pantry Management
- Automatic item tracking and expiration monitoring
- Barcode and image-based item scanning
- Intelligent categorization and unit conversion

### Recipe Intelligence
- AI-powered recipe recommendations based on available ingredients
- Personal preference filtering (dietary restrictions, cuisine preferences)
- Recipe completion with automatic inventory deduction

### Sustainability Focus
- Food waste reduction through smart recommendations
- Supply chain impact awareness
- Expiration tracking and usage optimization

## 🔗 External Integrations

- **USDA FoodData Central** - Nutritional information and standardized food data
- **Spoonacular API** - Recipe database and ingredient matching
- **Google Vision API** - Image recognition for item scanning
- **CrewAI** - Intelligent agent system for recommendations

## 📄 License

This project is part of a capstone project. See the main repository for license information.

---

**Need help?** Check the [troubleshooting guide](./getting-started/06-troubleshooting.md) or review the [full documentation index](./api/Doc_Start_Here.md).