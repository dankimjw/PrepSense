# PrepSense User Story Flowcharts

## Overview
PrepSense is a comprehensive pantry management application designed to help users reduce food waste by providing intelligent recipe recommendations based on available ingredients and expiration dates.

## Core User Story: Reducing Food Waste

### 1. Pantry Management Flow
```mermaid
flowchart TD
    A[User Opens PrepSense] --> B[Add Items to Pantry]
    B --> C{How to Add Items?}
    C -->|Manual Entry| D[Open Add Item Modal]
    C -->|OCR Scanning| E[Scan Receipt/Image]
    C -->|Shopping List| F[Check Items in Shopping List]
    
    D --> G[Select Category & Unit]
    G --> H[Set Expiration Date]
    H --> I[Save to Database]
    
    E --> J[AI Vision Analysis]
    J --> K[Extract Items & Quantities]
    K --> L[Review & Edit Items]
    L --> I
    
    F --> M[Add to Pantry Modal]
    M --> N[Set Units & Expiration]
    N --> I
    
    I --> O[Items Added to Pantry]
    O --> P[Expiration Tracking Enabled]
    P --> Q[Smart Recipe Recommendations]
```

### 2. Recipe Discovery & Food Waste Prevention
```mermaid
flowchart TD
    A[User Views Recipes] --> B{Recipe Source}
    B -->|From Pantry| C[Analyze Pantry Items]
    B -->|Discovery| D[Search/Filter Recipes]
    B -->|AI Chat| E[Chat with AI Assistant]
    
    C --> F[Prioritize Expiring Items]
    F --> G[Calculate Ingredient Matches]
    G --> H[Show Compatibility Scores]
    H --> I[Display Recipe Recommendations]
    
    D --> J[Apply Dietary Filters]
    J --> K[Search Recipe Database]
    K --> I
    
    E --> L[Natural Language Processing]
    L --> M[Generate Custom Recipes]
    M --> I
    
    I --> N[User Selects Recipe]
    N --> O[Recipe Detail View]
    O --> P{User Action}
    P -->|Quick Start| Q[Start Cooking Modal]
    P -->|Save Recipe| R[Add to My Recipes]
    P -->|Rate Recipe| S[Update Preferences]
    
    Q --> T[Recipe Completion Flow]
    T --> U[Update Pantry Quantities]
    U --> V[Reduce Food Waste]
```

### 3. Intelligent Cooking Assistant Flow
```mermaid
flowchart TD
    A[User Starts Cooking] --> B[Recipe Completion Modal]
    B --> C[Analyze Required Ingredients]
    C --> D[Match with Pantry Items]
    D --> E{Ingredient Availability}
    
    E -->|Available| F[Calculate Quantities to Use]
    E -->|Insufficient| G[Show Missing Items]
    E -->|Different Units| H[Smart Unit Conversion]
    
    F --> I[FIFO Algorithm - Use Oldest First]
    I --> J[Update Pantry Quantities]
    J --> K[Mark Items as Used]
    K --> L[Recipe Completed]
    
    G --> M[Suggest Alternatives]
    M --> N[Shopping List Integration]
    N --> O[Add Missing Items]
    O --> P[Continue Cooking]
    
    H --> Q[Ingredient-Specific Conversion]
    Q --> R[Volume/Weight/Count Conversion]
    R --> F
    
    L --> S[Track Cooking Stats]
    S --> T[Update Recipe Preferences]
    T --> U[Prevent Food Waste]
```

### 4. Smart Notifications & Expiration Management
```mermaid
flowchart TD
    A[Daily Background Check] --> B[Scan Pantry Items]
    B --> C[Check Expiration Dates]
    C --> D{Items Expiring Soon?}
    
    D -->|Yes| E[Generate Expiration Alerts]
    D -->|No| F[Continue Monitoring]
    
    E --> G[Prioritize by Expiration Date]
    G --> H[Find Recipes Using Expiring Items]
    H --> I[Send Smart Notifications]
    I --> J[User Opens App]
    
    J --> K[Recipe Suggestions Dashboard]
    K --> L[One-Tap Recipe Selection]
    L --> M[Quick Recipe Execution]
    M --> N[Consume Expiring Items]
    N --> O[Food Waste Prevented]
    
    F --> P[Weekly Stats Update]
    P --> Q[Track Waste Reduction]
    Q --> R[User Insights Dashboard]
```

### 5. Complete User Journey: Food Waste Reduction Cycle
```mermaid
flowchart TD
    A[User Buys Groceries] --> B[Add Items via OCR/Manual]
    B --> C[Items Stored in Pantry]
    C --> D[Expiration Tracking Active]
    D --> E[Daily Monitoring]
    
    E --> F{Items Expiring Soon?}
    F -->|Yes| G[Smart Recipe Recommendations]
    F -->|No| H[Continue Monitoring]
    
    G --> I[AI-Powered Recipe Matching]
    I --> J[User Selects Recipe]
    J --> K[Guided Cooking Experience]
    K --> L[Pantry Items Consumed]
    
    L --> M[Update Inventory]
    M --> N[Track Usage Stats]
    N --> O[Prevent Food Waste]
    
    H --> P[Regular Recipe Discovery]
    P --> Q[Maintain Pantry Rotation]
    Q --> R[Optimal Food Utilization]
    
    O --> S[User Behavior Analysis]
    S --> T[Improve Recommendations]
    T --> U[Better Waste Prevention]
    
    R --> V[Sustainable Food Habits]
    V --> W[Long-term Waste Reduction]
```

## Key Features That Enable Food Waste Reduction

### 1. **Intelligent Expiration Tracking**
- Automatic expiration date setting based on food categories
- Priority-based recipe recommendations for expiring items
- Proactive notifications before items spoil

### 2. **Smart Recipe Matching**
- AI-powered ingredient analysis
- Compatibility scoring for available ingredients
- Unit conversion system for precise measurements

### 3. **Seamless Pantry Management**
- OCR-powered receipt scanning
- Manual entry with smart categorization
- Shopping list integration with pantry

### 4. **Guided Cooking Experience**
- Step-by-step ingredient consumption tracking
- FIFO (First In, First Out) algorithm implementation
- Real-time pantry quantity updates

### 5. **Behavioral Learning System**
- Recipe rating and preference tracking
- Personalized recommendations based on usage patterns
- Continuous improvement of food waste prevention strategies

## Benefits to Users

1. **Reduced Food Waste**: Systematic tracking and utilization of pantry items
2. **Cost Savings**: Better ingredient utilization and meal planning
3. **Healthier Eating**: Diverse recipe recommendations based on available ingredients
4. **Time Efficiency**: Quick recipe discovery and cooking guidance
5. **Sustainable Living**: Contributing to environmental conservation through waste reduction

## Technical Implementation

- **Backend**: FastAPI with PostgreSQL for data persistence
- **Frontend**: React Native for cross-platform mobile experience
- **AI Integration**: OpenAI Vision API for OCR and recipe generation
- **Smart Algorithms**: Unit conversion, expiration tracking, and recipe matching
- **Cloud Infrastructure**: Google Cloud Platform for scalable deployment