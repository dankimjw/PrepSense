# PrepSense Modular Architecture Guide

## Overview
This guide explains the modular architecture implemented for the PrepSense iOS app to enable better team collaboration and prevent code conflicts.

## Directory Structure

```
ios-app/
├── app/
│   ├── (tabs)/
│   │   └── index.tsx        # Home screen (refactored to use modular components)
│   └── components/
│       └── CustomHeader.tsx  # Shared header component
│
├── components/
│   ├── home/                # Home screen specific components
│   │   ├── QuickActions.tsx # Quick action buttons section
│   │   ├── PantryItem.tsx   # Individual pantry item display
│   │   ├── PantryItemsList.tsx # List of pantry items
│   │   └── TipCard.tsx      # Storage tips display
│   ├── SearchBar.tsx        # Reusable search bar
│   └── FilterModal.tsx      # Reusable filter modal
│
├── hooks/
│   └── useItemsWithFilters.ts # Custom hook for items with filtering logic
│
├── utils/
│   ├── itemHelpers.ts       # Item formatting and styling utilities
│   └── encoding.ts          # Navigation parameter encoding utilities
│
├── context/
│   ├── ItemsContext.tsx     # Global items state management
│   └── AuthContext.tsx      # Global auth state management
│
└── types/
    └── index.ts             # Shared TypeScript interfaces

```

## Key Components

### 1. Custom Hooks
**`useItemsWithFilters`** - Encapsulates all item filtering and sorting logic
- Manages filter state (search, categories, sort)
- Provides filtered and sorted items
- Exports update functions for filters

### 2. Utility Functions
**`itemHelpers.ts`** - Contains all item-related helper functions:
- `getItemStyle()` - Returns icon and color based on item properties
- `formatExpirationDate()` - Formats expiration dates for display
- `calculateDaysUntilExpiry()` - Calculates days until expiration
- `getCategoryColor()` - Returns color for category badges
- `groupItems()` - Groups items by name and unit

### 3. Modular Components

#### Home Screen Components (`components/home/`)
- **QuickActions** - Displays action buttons (Add Item, Scan, Recipes, etc.)
- **PantryItem** - Individual item card with icon, details, and expiration
- **PantryItemsList** - Container for multiple pantry items with section header
- **TipCard** - Displays storage tips with icon

#### Shared Components
- **SearchBar** - Reusable search input with filter/sort buttons
- **FilterModal** - Modal for selecting categories and sort options
- **CustomHeader** - App-wide header with navigation and actions

## Working with the Architecture

### Adding New Features

1. **New Home Screen Section**
   - Create component in `components/home/`
   - Import and use in `index.tsx`
   - No need to modify existing sections

2. **New Utility Function**
   - Add to relevant file in `utils/`
   - Export and import where needed
   - Document the function purpose

3. **New Global State**
   - Create new context in `context/`
   - Or extend existing contexts carefully
   - Update types in `types/index.ts`

### Team Collaboration Guidelines

1. **Component Ownership**
   - Each component in `components/home/` can be owned by different team members
   - Changes to one component won't affect others

2. **State Management**
   - Use `useItemsWithFilters` hook for any item filtering needs
   - Don't duplicate filtering logic in components

3. **Styling**
   - Each component has its own StyleSheet
   - Use shared colors from `itemHelpers.ts` for consistency

4. **Type Safety**
   - Always define interfaces for component props
   - Use types from `types/index.ts` for consistency

### Example: Adding a New Feature

If you want to add a "Nutritional Summary" section to the home screen:

1. Create `components/home/NutritionalSummary.tsx`
2. Define the component with its own styles
3. Import and add to `index.tsx` where needed
4. No need to modify other components

```typescript
// components/home/NutritionalSummary.tsx
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface NutritionalSummaryProps {
  items: PantryItemData[];
}

export const NutritionalSummary: React.FC<NutritionalSummaryProps> = ({ items }) => {
  // Component implementation
};
```

## Benefits

1. **Reduced Merge Conflicts** - Components are isolated
2. **Easier Testing** - Each component can be tested independently
3. **Better Code Organization** - Clear separation of concerns
4. **Improved Reusability** - Components can be used elsewhere
5. **Parallel Development** - Multiple developers can work simultaneously

## Best Practices

1. **Keep Components Focused** - One component, one responsibility
2. **Use TypeScript** - Define interfaces for all props
3. **Document Complex Logic** - Add comments for non-obvious code
4. **Follow Naming Conventions** - Be consistent with existing patterns
5. **Test Your Changes** - Ensure components work in isolation