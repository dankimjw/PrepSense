# 🥦 PrepSense — Make Every Ingredient Count

**Capstone Project · University of Chicago MS in Applied Data Science (2025)**  
**Team:** Akash Sannidhanam, Daniel Kim, Bonny Mathew, Prahalad Ravi

---

## 🧭 Executive Summary

In today’s data-rich but time-poor society, managing food wisely is both a personal health goal and an environmental necessity. The U.S. alone wastes over 60 million tons of food annually—much of it due to expired or forgotten items in home kitchens. Consumers like our user persona “Lily” often shop with good intentions, but without tools to manage their pantry, they fall into wasteful cycles: buying items they already have, letting food expire, and struggling to decide what to cook.

**PrepSense** addresses this by transforming ordinary kitchens into smart, data-driven environments. This mobile-first AI platform enables users to scan their pantry, automatically track item expiry, receive health-conscious recipe suggestions based on what’s on hand, and reduce food waste in the process.

What began as a class project evolved into a comprehensive AI system powered by CrewAI, multimodal LLMs, and a seamless mobile interface. From image ingestion to personalized nutritional analysis, every aspect of PrepSense is modular, intelligent, and purpose-driven.

PrepSense is more than a technical project—it’s a blueprint for smarter living.

---

## 💡 Problem

Despite advances in food delivery and meal planning apps, none provide an intelligent link between pantry inventory and personalized, health-driven recipe generation. Meanwhile, consumers continue to:
- Waste money on food they forget to use
- Buy groceries without knowing what they already have
- Make unbalanced meals without nutrition insight
- Lack motivation to cook at home

The environmental and financial impact is staggering: $218 billion lost annually, and 30–40% of household food thrown away.

---

## 🎯 Business Objective

PrepSense sets out to create a tangible reduction in household food waste while supporting nutritional literacy and meal convenience. Its core business goals are to:

- Help users become more mindful of what’s in their kitchen
- Increase usage of perishables before expiry
- Reduce reliance on takeout by offering relevant recipes
- Encourage healthier eating through personalized insights
- Provide a scalable model that can integrate with retailers, nutrition services, or healthcare ecosystems

---

## 👩‍🍳 User Persona: Lily

Lily is a 30-year-old professional based in Dallas, TX. She prefers home-cooked meals and cares deeply about sustainability, but struggles with:

- Remembering what’s in her fridge
- Making meals that align with her health goals
- Preventing food waste

Her ideal solution is one that is mobile-first, fast, and “just works” without needing manual entry.

**PrepSense was built for Lily.**

---

## 📲 Product Experience

### 1. Pantry Tracking
Users take a photo of their pantry or receipt. Our system:
- Uses computer vision and LLMs to extract item names, brands, quantities, and expiry dates
- Automatically stores this structured data in a pantry database
- Displays items in a color-coded, user-editable inventory screen

### 2. Recipe Recommendation
Once pantry items are captured, users can:
- Receive personalized recipe suggestions that use up ingredients before they expire
- Filter by dietary goals (e.g., vegan, high-protein, low-sodium)
- Chat with an intelligent assistant to find ideas like “Quick lunch with tofu, no dairy”

### 3. Nutrition & Planning
PrepSense enhances the user’s decision-making by:
- Scoring recipes based on health metrics
- Highlighting macronutrient breakdowns
- Suggesting substitutions or add-ons for balance

### 4. Smart Shopping & Feedback
If an item is missing for a desired recipe:
- PrepSense recommends adding it to a shopping list
- Users can plan next grocery trips more intentionally

---
## 🏆 Competitive Advantage: How PrepSense Stands Out

PrepSense was developed not just as another pantry tracker or recipe generator, but as a fully integrated platform that intelligently bridges the gap between household food visibility, personalized nutrition, and environmental impact.

The table below compares PrepSense to several leading apps in the market:

| **Feature / Capability**         | **PrepSense** | **NoWaste** | **Yummly** | **Whisk** | **PantryCheck** |
|----------------------------------|---------------|-------------|------------|-----------|-----------------|
| Pantry Scanning                  | ✅             | ❌          | ❌         | ❌        | ❌              |
| Pantry Expiry Tracking           | ✅             | 🟣 Partial  | ❌         | ❌        | 🟣 Partial      |
| Smart Grocery List               | ✅             | ❌          | ❌         | ✅        | ✅              |
| Personalized Recipe Generation   | ✅             | ❌          | 🟢 Strong  | ❌        | ❌              |
| Recipe Scoring                   | ✅             | ❌          | ❌         | ✅        | ❌              |
| Adaptive to User Preferences     | 🟢 Emerging    | ❌          | 🟠 Basic   | 🟠 Basic  | ❌              |
| Sustainability Gamification      | 🟡 Roadmap     | ❌          | ❌         | ❌        | ❌              |

> ✅ = Fully implemented | 🟣 = Partial or limited | 🟠 = Basic version | 🟢 = In development | 🟡 = On roadmap

---

### 🔍 Why PrepSense Wins

- **Vision-Language Integration**: Photo-based pantry tracking using GPT-4o + Vision API is intuitive and reduces user burden.
- **Agent-Oriented Design**: PrepSense’s modular agent system (CrewAI) handles every stage from scanning to scoring, making it future-proof and extensible.
- **Health-first Personalization**: Nutrition-aware recipe generation prioritizes dietary needs, not just popularity.
- **Sustainability Intelligence**: By quantifying food waste, meal recovery, and CO₂ offsets, PrepSense uniquely empowers users to make an impact.
- **Gamification & Feedback Loops**: A planned sustainability dashboard and engagement features aim to keep users mindful and motivated.

PrepSense doesn’t just help users decide what to eat — it transforms how they think about food, health, and the planet.

---

## 🧠 Architecture: AI Orchestration with CrewAI

At the heart of PrepSense is an agentic pipeline powered by [**CrewAI**](https://github.com/joaomdmoura/crewai), which enables modular, memory-aware, and task-specific collaboration across AI agents.

| Agent           | Role                                                                 |
|------------------|----------------------------------------------------------------------|
| **BiteCam**        | Captures and pre-processes pantry or receipt images                 |
| **Scanner Sage**   | Extracts structured data via multimodal LLM and stores in DB        |
| **Fresh Filter**   | Identifies expired or spoiled items                                 |
| **NutriCheck**     | Computes nutritional values of generated meals                      |
| **HealthRanker**   | Scores meals based on dietary preferences and health guidelines     |
| **ChefParser**     | Converts LLM response into readable recipe format                   |
| **JudgeThyme**     | Validates if recipe is feasible with current pantry inventory       |
| **RecipeRover**    | Selects the best match based on nutrition, preferences, and timing  |

Each of these agents is orchestrated via CrewAI using memory tools, custom prompts, and response validation steps.

---

## ⚙️ Technical Implementation

| Component         | Technology                             |
|------------------|-----------------------------------------|
| Mobile Frontend   | React Native, Expo                     |
| Backend API       | FastAPI, Python                        |
| Database          | SQLite (dev), PostgreSQL (prod-ready)  |
| LLM Integration   | GPT-4o, chain-of-thought prompting      |
| Vision Processing | OpenAI Vision API, OCR & preprocessing |
| Agent Orchestration | CrewAI                               |
| Infrastructure    | GitHub Actions, Docker (planned)       |

---

## 🔄 Data Flow Overview

```
User Uploads Pantry Photo
        ↓
BiteCam + Scanner Sage → Extract items → Store in DB
        ↓
Fresh Filter → Remove expired items
        ↓
LLM + Prompt → Generate recipe list
        ↓
NutriCheck + HealthRanker → Score recipes
        ↓
ChefParser + JudgeThyme → Format & filter top recipe
        ↓
RecipeRover → Deliver final output to user
```

---

## 📈 Impact Projections

**Estimated Monthly Impact at 10,000 Users:**

| Metric                   | Projected Value               |
|--------------------------|-------------------------------|
| Meals Rescued            | 30,000+                       |
| Food Waste Avoided       | 100+ tons                     |
| Grocery Savings          | $1M+                          |
| CO₂ Offset               | 200+ metric tons              |
| Average Health Score ↑   | +25% dietary quality improvement |

---

## 🚀 Setup & Configuration

```bash
git clone https://github.com/dankimjw/PrepSense.git
cd PrepSense

# Backend setup
pip install -r requirements.txt

# Frontend setup
cd app
npm install
npx expo start
```

**.env Configuration**

```env
OPENAI_API_KEY=your_key
VISION_API_KEY=your_key
DATABASE_URL=sqlite:///./pantry.db
```

---

## 🛤 Roadmap (Post-Capstone)

- ✅ Functional MVP with pantry → recipe workflow
- ⏳ Grocery API integration (Instacart, Amazon Fresh)
- 👪 Family and household sharing mode
- 📊 Built-in analytics for users’ waste/savings
- 🧠 Offline mode with cached pantry state and recipes
- 🌍 Multilingual & cultural dietary support

---

## 🔍 Lessons Learned

Throughout 20 weeks of development, we encountered and overcame challenges across:
- Prompt design for accurate item extraction (e.g., dealing with blurry receipts)
- Ensuring privacy and efficiency in data processing
- Building reusable agent modules with CrewAI
- Balancing user preferences with nutritional health

We used agile sprints with weekly check-ins, peer reviews, and live demos.

---

## 🧑‍💻 Team & Contributions

- **Akash Sannidhanam** — CrewAI orchestration, agent logic, nutrition analytics  
- **Daniel Kim** — Backend development, database architecture, API integration  
- **Bonny Mathew** — Mobile UX/UI, recipe rendering, app state management  
- **Prahalad Ravi** — Image preprocessing, vision-to-text logic, LLM prompt tuning

We worked collaboratively using GitHub Projects and CI workflows.

---

## 📜 License & Acknowledgements

Licensed under the **MIT License**.  
Gratitude to:
- University of Chicago MSADS Faculty
- OpenAI (GPT-4o, Vision API)
- RTS Food Waste Research
- Expo / React Native Community
- The CrewAI Project

---

**PrepSense empowers people to cook smarter, waste less, and live healthier—one ingredient at a time.**

---

