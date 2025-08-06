# 🥦 PrepSense — Make Every Ingredient Count

**Capstone Project · University of Chicago MS in Applied Data Science (2025)**  
**Team:** Akash Sannidhanam, Daniel Kim, Bonny Mathew, Prahalad Ravi

---

## 🧭 Executive Summary

In today’s fast-paced world, consumers are increasingly making conscious choices about health, sustainability, and waste reduction. However, they often lack the tools to effectively manage their kitchen inventory and meal planning in a way that aligns with these values. PrepSense was created to solve this gap.

PrepSense is a mobile-first, AI-powered pantry and recipe assistant that empowers users to manage their food intelligently—from inventory tracking to personalized meal recommendations. Built as a capstone project for the University of Chicago’s MS in Applied Data Science program, PrepSense combines computer vision, CrewAI-powered agent orchestration, and personalized large language models (LLMs) to transform everyday household decisions into impactful actions.

The system works by allowing users to scan their pantry or receipts, automatically detecting items, quantities, and expiry dates. From there, it generates customized recipes based on what’s on hand, dietary restrictions, and personal preferences—minimizing waste while maximizing nutrition. Users are also given insight into nutritional content, missing items for recipes, and the ability to build a dynamic shopping list. This seamless end-to-end experience is enabled by a team of modular AI agents working in coordination through the CrewAI framework.

With food waste costing the U.S. over $218 billion annually, PrepSense represents not just a technological innovation—but a real opportunity to drive meaningful change at scale. At just 10,000 users, PrepSense could help rescue over 30,000 meals per month, reduce more than 100 tons of food waste, and deliver collective savings of over $1M annually.

PrepSense isn’t just a pantry tool—it’s a sustainability ally, a nutrition guide, and a smart kitchen companion.

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
## 🧪 How It Works

### 1. 📸 Scan Pantry or Receipt

Users begin by capturing a photo of their pantry or grocery haul.

<img width="589" height="1280" alt="image" src="https://github.com/user-attachments/assets/ec3cd5e6-3757-4d8d-8b6c-77b7224bcf73" />

### 2. 🤖 Item Detection

The system uses GPT-4o and vision models to identify and extract item names, quantities, categories, and expiry dates.

<img width="589" height="1280" alt="image" src="https://github.com/user-attachments/assets/bc98d2c5-46fa-4e0c-b4ee-e914b60ccfd2" />

Once processed, users can confirm and edit the recognized data.

### 3. 🧾 Pantry Dashboard

Items are automatically sorted by expiry date, and users can filter by category, freshness, or recent additions.

<img width="589" height="1280" alt="image" src="https://github.com/user-attachments/assets/9b7f36e0-7f75-490e-973b-70fad70d661d" />

From here, users can explore personalized recipe suggestions, generate a smart shopping list, and track impact metrics like food waste and money saved.

---
## 📲 Product Experience

### 1. Pantry Tracking
Users take a photo of their pantry or receipt. Our system:
- Uses computer vision and LLMs to extract item names, brands, quantities, and expiry dates
- Automatically stores this structured data in a pantry database
- Displays items in a color-coded, user-editable inventory screen

[Insert Screenshot]

### 2. Recipe Recommendation
Once pantry items are captured, users can:
- Receive personalized recipe suggestions that use up ingredients before they expire
- Filter by dietary goals (e.g., vegan, high-protein, low-sodium)
- Chat with an intelligent assistant to find ideas 

[Insert Screenshot]

### 3. Nutrition & Planning
PrepSense enhances the user’s decision-making by:
- Scoring recipes based on health metrics
- Highlighting macronutrient breakdowns
- Suggesting substitutions or add-ons for balance

[Insert Screenshot]

### 4. Smart Shopping & Feedback
If an item is missing for a desired recipe:
- PrepSense recommends adding it to a shopping list
- Users can plan next grocery trips more intentionally

[Insert Screenshot]

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
| Database          | PostgreSQL (prod-ready)  |
| LLM Integration   | GPT-4o, chain-of-thought prompting, Claude     |
| Vision Processing | OpenAI Vision API, OCR & preprocessing |
| Agent Orchestration | CrewAI                              |
| Infrastructure    | GitHub Actions, Docker (planned), Cloud Run      |

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

- **Akash Sannidhanam** 
- **Daniel Kim**
- **Bonny Mathew** 
- **Prahalad Ravi** 

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

