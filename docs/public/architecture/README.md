# 🏗️ Architecture Documentation

This directory contains system architecture documentation and design specifications for PrepSense.

## 📋 Architecture Overview

### System Design Documents
- **[PrepSense_User_Story_Flowcharts.md](./PrepSense_User_Story_Flowcharts.md)** - User journey flowcharts and interaction patterns
- **[Data Flows/](./Data%20Flows/)** - Data flow diagrams and screen navigation patterns
- **[FOOD_CATEGORIZATION_SYSTEM.md](./FOOD_CATEGORIZATION_SYSTEM.md)** - Food categorization and classification system
- **[USDA_INTEGRATION.md](./USDA_INTEGRATION.md)** - USDA FoodData Central integration architecture

### Feature Architecture
- **[SCAN_ITEMS_FEATURE.md](./SCAN_ITEMS_FEATURE.md)** - Image recognition and item scanning system
- **[MY_PANTRY_RECIPE_FLOW.md](./MY_PANTRY_RECIPE_FLOW.md)** - Pantry-to-recipe recommendation flow

## 🎯 System Architecture Overview

PrepSense follows a modern microservices architecture:

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   React Native  │    │   FastAPI        │    │   PostgreSQL    │
│   Frontend      │◄──►│   Backend        │◄──►│   Database      │
│   (iOS App)     │    │   (Python)       │    │   (Cloud SQL)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Expo/Metro    │    │  External APIs   │    │   Cloud Storage │
│   Development   │    │  • Spoonacular   │    │   • Images      │
│   Server        │    │  • USDA API      │    │   • Backups     │
│                 │    │  • Vision API    │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 📱 Frontend Architecture

The iOS app uses React Native with Expo and follows these patterns:
- **Screen-based navigation** with React Navigation
- **Component-based UI** with reusable components
- **State management** with React hooks and context
- **API integration** through service classes

## 🔌 Backend Architecture  

The FastAPI backend implements:
- **RESTful API design** with automatic OpenAPI documentation
- **Database abstraction** with SQLAlchemy ORM
- **External API integration** with caching and rate limiting
- **AI service integration** for image recognition and recommendations

## 🗄️ Database Architecture

PostgreSQL database hosted on Google Cloud SQL:
- **Normalized schema** for efficient queries
- **Foreign key relationships** for data integrity  
- **Indexes** for query performance
- **Migration system** for schema evolution

## 🔗 External Integrations

### USDA FoodData Central
- Nutritional information and standardized food data
- Unit conversion and ingredient normalization
- Category mapping for food classification

### Spoonacular API
- Recipe database with 330k+ recipes
- Ingredient matching and substitution
- Nutritional analysis and dietary filtering

### Google Vision API
- Image recognition for pantry item scanning
- OCR for reading product labels and expiration dates
- Object detection for food identification

## 📊 Data Flow Patterns

### Core Data Flows
1. **Item Scanning**: Image → Vision API → Item Recognition → Database Storage
2. **Recipe Matching**: Pantry Items → Algorithm → Recipe Recommendations → User Interface
3. **Recipe Completion**: Recipe Selection → Ingredient Deduction → Pantry Update → Analytics

### Caching Strategy
- **API Response Caching** for external service calls
- **Image Caching** for recipe and item photos
- **Query Result Caching** for frequently accessed data

## 🔄 Development Architecture

### Code Organization
```
PrepSense/
├── ios-app/                 # React Native frontend
│   ├── components/          # Reusable UI components  
│   ├── screens/            # Screen components
│   ├── services/           # API service classes
│   └── utils/              # Utility functions
├── backend_gateway/        # FastAPI backend
│   ├── app/               # Application code
│   ├── routers/           # API route handlers
│   ├── models/            # Database models
│   └── services/          # Business logic
└── docs/                  # Documentation
```

### Testing Architecture
- **Unit Tests** for individual components and functions
- **Integration Tests** for API endpoints and database operations
- **End-to-End Tests** for critical user flows
- **Performance Tests** for API response times and database queries

## 📈 Scalability Considerations

- **Horizontal scaling** through containerization
- **Database optimization** with proper indexing
- **Caching layers** for frequently accessed data
- **CDN integration** for static asset delivery

---

For implementation details, see the [API Documentation](../api/) section.