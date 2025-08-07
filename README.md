# 🥦 PrepSense — Make Every Ingredient Count

**Capstone Project · University of Chicago MS in Applied Data Science (2025)**  
**Team:** Akash Sannidhanam, Daniel Kim, Bonny Mathew, Prahalad Ravi

---
## 📑 Table of Contents
- [Project Motivation](#project-motivation)
- [User Persona](#user-persona)
- [Product Experience](#product-experience-flow)
- [Competitive Advantage](#competitive-advantage)
- [Why PrepSense Wins](#why-prepsense-wins)
- [Complete Architecture](#complete-architecture)
- [Data Flow Overview](#data-flow-overview)
- [Tech Stack](#tech-stack)
- [Impact Projections](#impact-projections)
- [Roadmap (Post-Capstone)](#roadmap-post-capstone)
- [Setup & Configuration](#setup-&-configuration)
- [Team & Contributions](#team-&-contributions)
- [License & Acknowledgements](#license-&-acknowledgements)

---

## 🧭 Project Motivation

Food waste is a global challenge with both environmental and personal costs. In the United States alone, nearly 60 million tons of food are wasted annually — valued at $218 billion — enough to feed 120 million people for a full year. Beyond the waste of resources, this contributes significantly to greenhouse gas emissions and climate change.

At the same time, many individuals — like Lily, our user persona — want to eat healthier, cook more at home, and reduce waste, but face daily challenges: manual pantry tracking, forgotten expiry dates, and difficulty planning balanced meals. These challenges often lead to last-minute takeout, skipped meals, or nutritionally imbalanced choices.

PrepSense was created to solve these problems on both fronts. By combining AI-powered pantry scanning, expiry tracking, and personalized recipe recommendations, it not only helps reduce waste but also supports healthier eating habits. The app considers nutritional balance, dietary preferences, and portion control — making it easier for users to prepare wholesome, home-cooked meals using what they already have.

**Our goal is to help people waste less, eat better, and live healthier, turning everyday meal preparation into a sustainable and health-conscious habit.**

Built as a capstone project for the University of Chicago’s MS in Applied Data Science program, PrepSense combines computer vision, CrewAI-powered agent orchestration, and the use of Multimodal large language models (LLMs) to transform everyday household decisions into impactful actions.

---

## 👩‍🍳 User Persona

Lily is a tech professional residing in San Diego. She is passionate about maintaining a healthy lifestyle, enjoys preparing nutritious home-cooked meals, and makes a weekly trip to the grocery store to stock her pantry. Lily is also deeply committed to sustainability and is mindful of how her daily choices impact the environment.

<img width="1920" height="1080" alt="PrepSense" src="https://github.com/user-attachments/assets/9f66e3ea-50a3-408a-b0e9-8dd4314e625c" />

Her challenges:

* Relies on manual pantry tracking — time-consuming and prone to error
* Forgets items in pantry or fridge until they expire → food waste
* Struggles to plan balanced meals with what she has on hand
* Occasionally resorts to less nutritious options when pressed for time
* Feels her food waste conflicts with her sustainability values

Her ideal solution is one that is mobile-first, smart, and “just works” without needing manual entry.

**PrepSense was built for Lily.**

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/cc085367-6a2d-44ba-a6ba-865e9a5939eb" />

---
## 📲 Product Experience

### 1. Pantry Updation Flow

**User Input**: 
1. Upload a photo of their pantry or receipt. 
2. Set dietary goals and cuisine preferences

**Our system**:
1. Uses computer vision, LLMs and Chain-of-Thought (CoT) logic to extract item names, brands, quantities, and expiry dates
2. Automatically stores this structured data in a pantry database

**User Output**: Displays items in a color-coded, manually-editable inventory screen

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/cabae70e-ecfd-4b31-9b08-dd009362a79b" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/37be8bab-803a-4fbf-84b7-dc445db1c3d0" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/82f2e1ee-5712-4891-ba5b-ee25df62d670" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/f737a299-6654-4f27-9e51-9e4520096b54" />

### 2. Recipe Generation Flow

**Input**: User Pantry Item list

**Our system**:
Engages multiple AI agents to read from pantry, filter out unexpired items, incorporate user’s taste preferences, search for recipe, score recipe based on nutritional value, generates recipe image, evaluate the results are accurate and formats it to a readable format.

<img width="1600" height="900" alt="image" src="https://github.com/user-attachments/assets/195a34e1-ab63-4140-bce7-c1e2f32878e0" />

Once pantry items are captured, users can:
1. Receive personalized recipe suggestions that use up ingredients before they expire
2. Filter by dietary goals (e.g., vegan, high-protein, low-sodium)
3. Chat with an intelligent assistant to find ideas like “Quick lunch with tofu, no dairy”
4. Manual pantry run down option


<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/0a8e202c-2186-4374-b0ee-1a0fefb7ecc9" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/e0378d3b-412f-4626-b75d-a0106368c4c0" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/4d847994-793a-4520-af64-19622ba06173" />

### 3. Smart Shopping & Feedback

If an item is missing for a desired recipe:
- PrepSense recommends adding it to a shopping list
- Users can plan next grocery trips more intentionally

Users can also get useful summary stats on their consumption, food saved and impact on the environment.

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/4355b74b-e8b2-4867-8b1b-7a2c3a2eafd2" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/4c7245ac-82f9-488f-a2af-4e52601d73a1" />


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

## 🧠 Architecture: 

<img width="1017" height="571" alt="PrepSense Architecture diagram" src="https://github.com/user-attachments/assets/fbc6b935-ef3b-4536-8279-85b9a3ec5be4" />


At the heart of PrepSense is an agentic pipeline powered by [**CrewAI**](https://github.com/joaomdmoura/crewai), which enables modular, memory-aware, and task-specific collaboration across AI agents.


| Agent         | Role |
|---------------|------|
| **Scanner Sage** | Reads pantry items from the database |
| **Fresh Filter** | Removes expired or unusable items |
| **Taster Tune** | Applies dietary restrictions/preferences stored in database |
| **Recipe Rover** | Generates recipe suggestions |
| **Nutri Check** | Evaluates nutritional balance |
| **Health Ranker** | Scores meals based on dietary preferences and health guidelines  |
| **Judge Thyme** | Validates if recipe is feasible with current pantry inventory |
| **Bite Cam** | Creates recipe image |
| **Chef Parser** | Formats recipe output for UI |


Each of these agents is orchestrated via CrewAI using memory tools, custom prompts, and response validation steps.

---

## 🔄 Data Flow Overview


```
User Uploads Pantry Photo (details extracted and stored in PantryDB)
        ↓
Scanner Sage → Extract pantry items 
        ↓
Fresh Filter → Remove expired or duplicate items
        ↓
TasterTune → Personalize based on user preferences (from UserDB)
        ↓
LLM + RecipeRover → Generate initial recipe list
        ↓
NutriCheck + HealthRanker → Score recipes based on nutrition and dietary goals
        ↓
JudgeThyme → Refine and filter the top recipe based on accuracy & feasibility
        ↓
ChefParser → Deliver final output (recipe + insights) to user
```

---


## ⚙️ Tech Stack

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


---

## 🌍 Impact Projections

PrepSense is designed not just to make meal planning easier but to drive measurable sustainability and cost-saving outcomes.

**Estimated per Household Impact** (based on pilot data & market research):
- **5% lower food waste per household**
- ~**60 lbs** of food saved annually through pantry-based planning and expiry alerts
- **$400 saved per year** (~75 meals rescued)
- ~**120 kg of CO₂ emissions prevented**

These figures compound significantly as PrepSense adoption grows. For example, with **10,000 active households**:
- **600,000 lbs** of food saved
- **$4 million** in total savings
- **1.2 million kg of CO₂ emissions prevented**
---

## 🛤 Roadmap (Post-Capstone)

- ⏳ Grocery API integration (Instacart, Amazon Fresh)
- 👪 Family and household sharing mode
- 📊 Built-in analytics for users’ waste/savings
- 🧠 Offline mode with cached pantry state and recipes
- 🌍 Multilingual & cultural dietary support

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

**PrepSense empowers people to waste less, eat better, and live healthier, turning everyday meal preparation into a sustainable and health-conscious habit**

---

