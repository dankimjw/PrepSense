# iOS Frontend Documentation

## 🚨 CRITICAL INSTRUCTIONS FOR ALL CLAUDE INSTANCES 🚨

**BEFORE making any changes to the iOS app:**
1. **READ** this document to understand app architecture
2. **CHECK** actual implementation in ios-app/ directory
3. **TEST** on iOS simulator before documenting changes
4. **UPDATE** this document immediately after modifying screens/components
5. **MAINTAIN** consistency with existing patterns

**This is LIVE DOCUMENTATION** - Keep it synchronized with ios-app/ implementation!

---

## App Architecture

### Technology Stack
- **Framework**: React Native with Expo
- **Navigation**: Expo Router (file-based routing)
- **State Management**: React Context API
- **Styling**: StyleSheet API
- **API Client**: Custom fetch-based client
- **Testing**: Jest + React Native Testing Library

### Directory Structure
```
ios-app/
├── app/                    # Screens (Expo Router)
│   ├── (tabs)/            # Tab navigation screens
│   │   ├── index.tsx      # Home/Pantry screen
│   │   ├── recipes.tsx    # Recipes discovery
│   │   ├── chat.tsx       # AI Chat
│   │   ├── stats.tsx      # Statistics
│   │   └── admin.tsx      # Admin panel
│   ├── _layout.tsx        # Root layout
│   └── [screen].tsx       # Other screens
├── components/            # Reusable components
├── services/              # API and business logic
├── context/               # React Context providers
├── hooks/                 # Custom React hooks
├── utils/                 # Helper functions
└── constants/             # App constants
```

---

## Main Screens

### 1. Home Screen (`app/(tabs)/index.tsx`)
**Purpose**: Display and manage pantry items

**Key Features**:
- Display pantry items with expiration tracking
- Search and filter functionality
- Quick actions (Scan Items, Recipes, Shopping List)
- Sort by name/expiry with toggle
- Item grouping by name and unit

**API Calls**:
```typescript
fetchPantryItems(111) // Get all pantry items
deletePantryItem(itemId) // Delete item
updatePantryItem(itemId, data) // Update item
```

**Components Used**:
- `SearchBar` - Search functionality
- `FilterModal` - Category/expiry filters
- `QuickActions` - Action buttons
- `PantryItemsList` - Item display
- `WasteImpactCard` - Environmental impact

### 2. Recipes Screen (`app/(tabs)/recipes.tsx`)
**Purpose**: Discover recipes based on pantry items

**Tabs**:
- "For You" - Personalized recommendations
- "From Pantry" - Using available ingredients
- "Discover" - All recipes

**API Calls**:
```typescript
fetch('/api/v1/recipes/search?user_id=111')
fetch('/api/v1/recipes/search?ingredients_available=true')
```

### 3. Chat Screen (`app/(tabs)/chat.tsx`)
**Purpose**: AI-powered recipe recommendations

**Features**:
- Real-time chat interface
- Recipe suggestions based on preferences
- Quick actions for common requests

**API Calls**:
```typescript
fetch('/api/v1/chat/message', {
  method: 'POST',
  body: JSON.stringify({
    message: userMessage,
    user_id: 111,
    use_preferences: true
  })
})
```

### 4. Stats Screen (`app/(tabs)/stats.tsx`)
**Purpose**: Display usage statistics and insights

**Features**:
- Pantry analytics (total, expired, expiring)
- Recipe cooking history
- Environmental impact metrics
- Time range selector (week/month/year)
- Unit toggle (metric/imperial)

**API Calls**:
```typescript
fetch('/api/v1/stats/comprehensive?user_id=111&timeframe=month')
fetch('/api/v1/cooking-history/trends?user_id=111&days=7')
fetch('/api/v1/user-recipes')
```

### 5. Admin Screen (`app/(tabs)/admin.tsx`)
**Purpose**: Development tools and mock data control

**Features**:
- User management (currently mock data)
- Remote control toggles for mock features
- Database table checking
- Test scenarios

---

## Key Components

### Modals

#### 1. `AddItemModalV2`
- Add new pantry items
- Auto-completion for common items
- Category selection
- Expiration date picker

#### 2. `ConsumptionModal`
- Track item consumption
- Quick amount buttons
- Custom amount input
- Updates pantry quantities

#### 3. `RecipeCompletionModal`
- Mark recipe as completed
- Shows ingredients used
- Updates pantry inventory

#### 4. `FilterModal`
- Filter by categories
- Filter by expiration status
- Multi-select interface

### Home Components

#### 1. `PantryItem`
**File**: `components/home/PantryItem.tsx`

**Props**:
```typescript
{
  item: PantryItemData
  onPress: (item: PantryItemData) => void
  onEditPress?: (item: PantryItemData) => void
  onDelete?: (item: PantryItemData) => void
}
```

**Features**:
- Expiration date display with urgency colors
- **Swipe-to-delete functionality** (swipe left to reveal delete button)
- Category tags with background colors
- Icons with MaterialIcons/MaterialCommunityIcons
- Quantity display with proper formatting
- Three-dot menu for additional actions

**Swipe-to-Delete Implementation**:
- Uses `react-native-gesture-handler/Swipeable`
- Requires app to be wrapped with `GestureHandlerRootView` in `app/_layout.tsx`
- Red delete button with trash icon appears on swipe left
- Calls `deletePantryItem` API to remove from database
- Immediate deletion without confirmation for better UX

#### 2. `QuickActions`
- Scan Items → Receipt/item scanning
- Find Recipes → Recipe discovery
- Shopping List → List management

---

## API Service Layer

### Main API Service (`services/api.ts`)

**Key Functions**:
```typescript
// Pantry Management
fetchPantryItems(userId: number): Promise<PantryItem[]>
savePantryItem(userId: number, item: PantryItem): Promise<void>
updatePantryItem(itemId: string, updates: Partial<PantryItem>): Promise<void>
deletePantryItem(itemId: string): Promise<void>

// Recipe Operations
searchRecipes(params: SearchParams): Promise<Recipe[]>
getRecipeDetails(recipeId: number): Promise<RecipeDetails>
completeRecipe(recipeId: number, ingredients: RecipeIngredient[]): Promise<void>

// User Preferences
fetchUserPreferences(userId: number): Promise<UserPreferences>
updateUserPreferences(userId: number, prefs: UserPreferences): Promise<void>
```

### API Client (`services/apiClient.ts`)
- Centralized error handling
- Request/response logging
- Base URL configuration
- JSON parsing

---

## State Management

### Contexts

#### 1. `AuthContext`
- User authentication state
- Mock token for development
- User profile management

#### 2. `ItemsContext`
- Pantry items state
- CRUD operations
- Real-time updates

### Custom Hooks

#### 1. `useItemsWithFilters`
- Combines items with filter state
- Search functionality
- Category/expiry filtering

#### 2. `useSupplyChainImpact`
- Environmental impact calculations
- Supply chain waste metrics

---

## Navigation Flow

```
Root (_layout.tsx)
├── (tabs) [Tab Navigator]
│   ├── Home (index.tsx)
│   ├── Recipes (recipes.tsx)
│   ├── Chat (chat.tsx)
│   ├── Stats (stats.tsx)
│   └── Admin (admin.tsx)
├── recipe-details.tsx
├── cooking-mode.tsx
├── scan-items.tsx
├── receipt-scanner.tsx
├── items-detected.tsx
└── recipe-spoonacular-detail.tsx
```

---

## Testing

### Test Structure
```
__tests__/
├── components/        # Component tests
├── screens/          # Screen tests
├── hooks/            # Hook tests
└── integration/      # Integration tests
```

### Running Tests
```bash
cd ios-app
npm test                    # Run all tests
npm test ComponentName      # Run specific test
npm test -- --coverage      # With coverage
```

---

## Environment Configuration

### Key Environment Variables
```
EXPO_PUBLIC_API_BASE_URL    # Backend API URL
EXPO_PUBLIC_SUPPRESS_WARNINGS # Warning suppression
```

### Configuration Files
- `app.json` - Expo configuration
- `babel.config.js` - Babel setup
- `jest.config.js` - Test configuration
- `tsconfig.json` - TypeScript config

---

## Common Patterns

### API Error Handling
```typescript
try {
  const data = await fetchPantryItems(userId);
  setItems(data);
} catch (error) {
  console.error('Error:', error);
  Alert.alert('Error', 'Failed to load items');
}
```

### Loading States
```typescript
const [isLoading, setIsLoading] = useState(false);
// Show ActivityIndicator when isLoading is true
```

### Refresh Control
```typescript
<ScrollView
  refreshControl={
    <RefreshControl
      refreshing={refreshing}
      onRefresh={onRefresh}
    />
  }
>
```

---

## Styling Guidelines

### Color Palette
- Primary Green: `#297A56`
- Success: `#10B981`
- Warning: `#F59E0B`
- Error: `#DC2626`
- Background: `#f5f5f5`

### Common Styles
- Border Radius: 8-16px
- Shadow: iOS shadow properties
- Spacing: 8, 12, 16, 20, 24px

---

**Last Updated**: 2025-07-27
**Next Review**: When adding new screens or major components

<!-- AUTO‑DOC‑MAINTAINER: FrontEnd_iOS -->
<!-- END -->