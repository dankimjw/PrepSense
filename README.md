# 🥦 PrepSense — Make Every Ingredient Count

**Capstone Project · University of Chicago MS in Applied Data Science (2025)**  
**Team:** Akash Sannidhanam, Daniel Kim, Bonny Mathew, Prahalad Ravi

---

## 🧭 Executive Summary

Food waste is a global challenge with both environmental and personal costs. In the United States alone, nearly 60 million tons of food are wasted annually — valued at $218 billion — enough to feed 120 million people for a full year. Beyond the waste of resources, this contributes significantly to greenhouse gas emissions and climate change.

At the same time, many individuals — like Lily, our user persona — want to eat healthier, cook more at home, and reduce waste, but face daily challenges: manual pantry tracking, forgotten expiry dates, and difficulty planning balanced meals. These challenges often lead to last-minute takeout, skipped meals, or nutritionally imbalanced choices.

PrepSense was created to solve these problems on both fronts. By combining AI-powered pantry scanning, expiry tracking, and personalized recipe recommendations, it not only helps reduce waste but also supports healthier eating habits. The app considers nutritional balance, dietary preferences, and portion control — making it easier for users to prepare wholesome, home-cooked meals using what they already have.

Our goal is to help people waste less, eat better, and live healthier, turning everyday meal preparation into a sustainable and health-conscious habit.

Built as a capstone project for the University of Chicago’s MS in Applied Data Science program, PrepSense combines computer vision, CrewAI-powered agent orchestration, and the use of Multimodal large language models (LLMs) to transform everyday household decisions into impactful actions.

---

## 👩‍🍳 User Persona: Lily

Lily is a tech professional residing in San Diego. She is passionate about maintaining a healthy lifestyle, enjoys preparing nutritious home-cooked meals, and makes a weekly trip to the grocery store to stock her pantry. Lily is also deeply committed to sustainability and is mindful of how her daily choices impact the environment.

<img width="1920" height="1080" alt="PrepSense" src="https://github.com/user-attachments/assets/9f66e3ea-50a3-408a-b0e9-8dd4314e625c" />

Her challenges:

Relies on manual pantry tracking — time-consuming and prone to error
Forgets items in pantry or fridge until they expire → food waste
Struggles to plan balanced meals with what she has on hand
Occasionally resorts to less nutritious options when pressed for time
Feels her food waste conflicts with her sustainability values

Her ideal solution is one that is mobile-first, smart, and “just works” without needing manual entry.

**PrepSense was built for Lily.**

[app screenshot]


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

