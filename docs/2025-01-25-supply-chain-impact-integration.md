# Supply Chain Impact UI Integration Guide

## Where to Add Supply Chain Impact Data

### 1. **Home Screen Integration** 🏠
**Component**: `WasteImpactCard.tsx`
**Placement**: Below pantry summary, above recipe suggestions

```typescript
// In home screen
<PantrySummary />
<WasteImpactCard 
  expiringItems={expiringItems}
  onPress={() => navigation.navigate('SupplyChainImpact')}
/>
<RecipeSuggestions />
```

**What it shows**:
- Real-time CO₂ impact of expiring items
- Economic value at risk
- Supply chain multiplier effect
- "URGENT" badge for high-risk days

### 2. **Dedicated Impact Stats Screen** 📊
**Component**: `SupplyChainImpactStats.tsx`
**Navigation**: Via WasteImpactCard tap or stats menu

**Three tabs**:
- **Today**: Current items at risk with multiplier breakdown
- **Trends**: Weekly prevention vs waste with achievements
- **Impact Guide**: Educational content about supply chain losses

### 3. **Individual Item Details** 🔍
**Enhancement**: Add to existing food item screens

```typescript
// In pantry item detail
<EnvironmentalImpact 
  ghgPerKg={item.co2PerKg}
  supplyChainMultiplier={2.52}
  compact={false}
/>
```

### 4. **Recipe Suggestions Enhancement** 🍳
**Update**: Existing recipe cards to show waste reduction potential

```typescript
// In recipe card
<Text style={styles.wasteReductionBadge}>
  Saves {totalCO2Prevented}kg CO₂e from supply chain
</Text>
```

## API Endpoints

### New Routes Added:
- `GET /api/v1/supply-chain-impact/today-impact/{user_id}`
- `GET /api/v1/supply-chain-impact/supply-chain-guide`
- `GET /api/v1/supply-chain-impact/weekly-trends/{user_id}`

### Enhanced Existing:
- Waste reduction endpoints now include supply chain multipliers
- Environmental impact calculations amplified by upstream losses

## Key Data Points to Display

### 1. **Home Screen Alert** (Daily)
```
🌍 Waste Impact Alert - URGENT
45.3 kg CO₂e    $28.50 at risk    98.2kg produced
= 113 miles      economic value    supply chain

💡 7 items expiring soon. Preventing their waste 
   saves the entire supply chain impact!

Tap to see waste-smart recipes →
```

### 2. **Today's Impact** (Detail Screen)
```
Today's Impact
45.3 kg CO₂e at risk    2.2x supply chain impact

🛈 For every 1kg you waste, 2.2kg was originally 
  produced across the supply chain

Supply Chain Breakdown:
Food reaching your kitchen: 45%
Lost at farm & harvest: 25%
Lost in transport & storage: 20%
Lost at retail: 10%
```

### 3. **Weekly Trends**
```
This Week's Impact
✅ 12 items saved    ❌ 3 items wasted    🍃 89.7 kg CO₂e saved

🌟 Great job! You saved the equivalent of:
• 224 miles of driving
• Prevented 26.4kg of upstream production waste
```

### 4. **Supply Chain Guide** (Educational)
```
Supply Chain Multipliers
How much was originally produced for each food type

Lettuce                                    5.7x
82.5% lost in supply chain
CO₂: 1.5 kg/kg → 8.6 kg/kg wasted

Tomatoes                                   2.52x  
60.3% lost before reaching you
CO₂: 2.09 kg/kg → 5.3 kg/kg wasted
```

## User Flow

1. **Discovery**: User sees WasteImpactCard on home screen
2. **Engagement**: Taps to see detailed supply chain impact
3. **Education**: Learns about multiplier effect in Impact Guide
4. **Action**: Uses waste-smart recipe suggestions
5. **Tracking**: Sees prevention progress in weekly trends
6. **Motivation**: Achievements and CO₂ savings feedback

## Technical Implementation

### Data Flow:
1. **Pantry items** → Check expiry dates
2. **Food types** → Look up supply chain multipliers  
3. **Environmental data** → Apply multiplier effect
4. **Real-time calculation** → Show amplified impact
5. **Historical tracking** → Track prevention vs waste

### Calculations:
```typescript
// Supply chain multiplier by food type
const multipliers = {
  'lettuce': 5.7,   // 82.5% supply chain loss
  'tomatoes': 2.52, // 60.3% supply chain loss  
  'bananas': 2.86,  // 65% supply chain loss
  'rice': 1.60,     // 37.7% supply chain loss
  'beef': 1.8       // 44.4% supply chain loss
};

// Amplified CO₂ impact
const realCO2Impact = baseCO2PerKg * multiplier;
```

## Messaging Strategy

### Key Messages:
1. **"For every 1kg wasted, 2.5kg was produced"** - Shows hidden impact
2. **"Preventing waste saves the entire journey"** - Emphasizes upstream benefit  
3. **"Fresh produce has 3x supply chain impact"** - Prioritizes high-impact items
4. **"You saved 89kg CO₂e this week"** - Positive reinforcement

### Emotional Hooks:
- 🚨 **Urgency**: "URGENT - High impact items expiring today"
- 🌍 **Scale**: "= 113 miles of driving prevented"  
- 🌟 **Achievement**: "Great job! You're saving the planet"
- 💡 **Education**: "Did you know? Only 17% of lettuce reaches consumers"

## Benefits of This Integration

1. **2-3x More Compelling**: Shows true environmental impact
2. **Educational**: Users learn about food system waste
3. **Actionable**: Prioritizes highest-impact items
4. **Motivational**: Bigger numbers = more engagement
5. **Differentiated**: Unique insight not available elsewhere

This turns PrepSense from "save this food" into "save the entire food system journey"!