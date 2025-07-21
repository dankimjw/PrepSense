# Scan Items Feature Implementation

## Overview
The Scan Items feature replaces the "Add Item" quick action button with a new "Scan Items" button that allows users to quickly add pantry items by scanning barcodes or taking photos of products.

## User Flow
1. User taps "Scan Items" button from home screen quick actions
2. User can either:
   - Take a photo using camera
   - Select an image from gallery
3. Backend processes the image to identify:
   - Product name and brand
   - Barcode (if visible)
   - Category and unit information
   - Suggested expiration date based on product type
4. User is redirected to items-detected screen to:
   - Review detected items
   - Edit quantities, units, or names
   - Confirm and add items to pantry

## Technical Implementation

### Frontend Changes
1. **QuickActions Component** (`ios-app/components/home/QuickActions.tsx`)
   - Replaced "Add Item" (id: 'add') with "Scan Items" (id: 'scan-items')
   - Changed icon from 'add-circle' to 'barcode'
   - Route now points to '/scan-items'

2. **Scan Items Screen** (`ios-app/app/scan-items.tsx`)
   - New screen for image capture/selection
   - Uses expo-image-picker for camera and gallery access
   - Sends base64 encoded images to backend
   - Handles permission requests for camera/gallery
   - Shows scanning progress with loading overlay
   - Navigates to items-detected screen with results

### Backend Changes
1. **OCR Router Enhancement** (`backend_gateway/routers/ocr_router.py`)
   - Added new `/ocr/scan-items` endpoint
   - Supports two scan types:
     - `barcode`: Optimized for barcode and product package scanning
     - `pantry_item`: General product identification
   - Uses OpenAI Vision API (gpt-4o-mini) for image analysis
   - Returns structured data with:
     - Product name, brand, and display name
     - Quantity and appropriate units
     - Category (auto-detected or categorized)
     - Barcode number (if visible)
     - Nutrition information (if available)
     - Default expiration dates based on category

2. **Enhanced ParsedItem Model**
   - Added fields for barcode, brand, product_name, nutrition_info, expiration_date
   - Supports richer product information from scans

## Key Features
- **Smart Product Recognition**: Identifies products from labels, text, and barcodes
- **Brand Detection**: Extracts and includes brand information
- **Category Assignment**: Automatically categorizes items or uses AI categorization
- **Expiration Prediction**: Sets intelligent default expiration dates based on product type
- **Nutrition Extraction**: Captures nutrition facts when visible
- **Flexible Scanning**: Works with barcodes, product labels, or general item photos

## Integration Points
- Uses existing `items-detected` screen for item review/editing
- Leverages existing pantry item addition flow
- Compatible with existing categorization service
- Works with current user authentication (uses user ID from context)

## Future Enhancements
- Batch scanning (multiple items in one photo)
- Barcode database integration for faster lookups
- Receipt + individual item scanning combination
- Store price tracking from scanned items
- Inventory suggestions based on scanned items