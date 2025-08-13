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

PrepSense was created to solve these problems on both fronts. By combining a fully integrated AI-powered pantry scanning, expiry tracking, and personalized recipe recommendations, it not only helps reduce waste but also supports healthier eating habits. The app considers nutritional balance, dietary preferences, and portion control — making it easier for users to prepare wholesome, home-cooked meals using what they already have.

**Our goal is to help people waste less, eat better, and live healthier, turning everyday meal preparation into a sustainable and health-conscious habit.**

Built as a capstone project for the University of Chicago’s MS in Applied Data Science program, PrepSense combines computer vision, CrewAI-powered Agentic AI state management, and the use of Multimodal large language models (LLMs) to transform everyday household decisions into impactful actions.

---

## 👩‍🍳 User Persona

Lily is a tech professional residing in San Diego. She is passionate about maintaining a healthy lifestyle, enjoys preparing nutritious home-cooked meals, and makes a weekly trip to the grocery store to stock her pantry. Lily is also deeply committed to sustainability and is mindful of how her daily choices impact the environment.

<img width="1164" height="627" alt="image" src="https://github.com/user-attachments/assets/2be2ca9c-0aa2-48ab-8aad-f59f82d9fc07" />

Her challenges:

* Relies on manual pantry tracking — time-consuming and prone to error
* Forgets items in pantry or fridge until they expire, leading to food waste
* Struggles to plan balanced meals with what she has on hand
* Occasionally resorts to less nutritious options when pressed for time
* Feels her food waste conflicts with her sustainability values

Her ideal solution is one that is mobile-first, smart, and “just works” without needing manual entry.

**PrepSense was built for Lily.**

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/cc085367-6a2d-44ba-a6ba-865e9a5939eb" />

---
## 📲 Product Workflow

### 1. Pantry Updation Flow

**User Input**: 
1. Upload a photo of their pantry or receipt. 

**Our system**:
1. Image is processed by a Multimodal LLM
2. Sequential Chain-of-Thought (CoT) logic to detect, classify, and then attribute extraction for brand, category, quantity, and expiry date.
3. Output returned as a structured JSON object that is then parsed, and stored in a structured pantry database

**User Output**: Displays items in a color-coded, manually-editable inventory screen

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/cabae70e-ecfd-4b31-9b08-dd009362a79b" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/37be8bab-803a-4fbf-84b7-dc445db1c3d0" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/82f2e1ee-5712-4891-ba5b-ee25df62d670" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/f737a299-6654-4f27-9e51-9e4520096b54" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/801f0e28-f48b-4738-bf8d-8b5bdedf9466" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/89020849-ea98-44b8-b9d0-25479adc16a6" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/d178dd76-80fe-41f3-bfe6-85bb31fd6714" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/a3fe375b-fddc-4b6b-bfe1-bc73e0f60d48" />


### 2. Recipe Generation Flow

**Input**: 
1. User Pantry Item list
2. Saved user diet and cuisine preference

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/82f2e1ee-5712-4891-ba5b-ee25df62d670" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/834a85e8-d983-4d99-9915-bd9fa418b4bc" />


**Our system**:
Engages an Agent Orchestrator, which is a coordinated sequence of specialised agents — each with a distinct role:
| Agent         | Role |
|---------------|------|
| **Scanner Sage** | Reads pantry items from the database |
| **Taster Tune** | Applies dietary restrictions/preferences stored in database |
| **Filter Fresh** | Removes expired or unusable items |
| **Recipe Rover** | Generates recipe suggestions |
| **Health Ranker** | Scores meals based on dietary preferences and health guidelines  |
| **Judge Thyme** | Validates if recipe is feasible with current pantry inventory |
| **Bite Cam** | Creates recipe image |
| **Chef Parser** | Formats recipe output for UI |


Each of these agents is orchestrated via CrewAI using memory tools, custom prompts, and response validation steps.

<img width="1163" height="616" alt="image" src="https://github.com/user-attachments/assets/6ca447b4-6094-492e-bda4-40359ccefb95" />

Once pantry items are captured, users can:
1. Receive personalized recipe suggestions based on whats in their pantry.
2. Filter by dietary goals (e.g., vegan, high-protein, low-sodium)
3. Chat with an AI Chef to find ideas like “Quick lunch with tofu, no dairy”
4. Manually update pantry based on items consumed

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/a9b87fa0-f23c-4fac-9a0b-cfe478330468" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/73c9b8a5-5acf-4794-b304-8964b9c7788d" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/7862f5ed-7990-491c-99f9-50084036cde5" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/e0378d3b-412f-4626-b75d-a0106368c4c0" />

### 3. Pantry Rundown Flow

Once a recipe is chosen to be made:
- PrepSense removes ingredients used in that recipe from the live pantry db
- Optionally, Users can choose to manually remove items they might have consumed from the pantry

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/4d847994-793a-4520-af64-19622ba06173" />

### 4. Smart Shopping & Feedback

If an item is missing for a desired recipe:
- PrepSense recommends adding it to a shopping list
- Users can plan next grocery trips more intentionally

Users can also get useful summary stats on their consumption, food saved and impact on the environment.

<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/b43bf7c7-c79c-4e0c-8a84-7764ea8633a3" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/483b348f-e696-45ab-9eb2-361af51714bb" />
<img width="272" height="597" alt="image" src="https://github.com/user-attachments/assets/0c5164a0-adab-4afe-825c-9ad6e3b4213d" />




---
## 🏆 Competitive Advantage: How PrepSense Stands Out

PrepSense is both your Pantry Manager and Personal AI Chef. By integrating a fully AI-powered platform it intelligently bridges the gap between household food visibility, personalized nutrition, and environmental impact.

The table below compares PrepSense to several leading apps in the market:

| **Feature / Capability**         | **PrepSense** | **NoWaste** | **Yummly** | **Whisk** | **PantryCheck** |
|----------------------------------|---------------|-------------|------------|-----------|-----------------|
| Pantry Scanning                  | ✅             | ✅          | ❌         | ❌        | ✅              |
| Pantry Expiry Tracking           | ✅             | ✅          | ❌         | ❌        | ✅              |
| Smart Grocery List               | ✅             | ✅          | ✅         | ✅        | ✅              |
| Personalized Recipe Generation   | ✅             | ❌          | ✅         | ✅        | ❌              |
| Adaptive to User Preferences     | 🟢 Emerging    | ❌          | ✅         | 🟠 Basic  | ❌              |
| Sustainability Gamification      | 🟡 Roadmap     | ✅          | ❌         | ❌        | ❌              |
| Grocery Store API Integration    | 🟡 Roadmap     | ❌          | ✅         | ❌        | 🟠 Basic              |

> ✅ = Fully implemented | 🟠 = Basic version | 🟢 = In development | 🟡 = On roadmap

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


<img width="1017" height="571" alt="image" src="https://github.com/user-attachments/assets/c757cd5c-17db-4a24-8a51-8fb3958d4394" />


At the heart of PrepSense is an agentic pipeline powered by [**CrewAI**](https://github.com/joaomdmoura/crewai), which enables modular, memory-aware, and task-specific collaboration across AI agents.

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
| External API      | Spoonacular API                              |
| Image Generation | OpenAI                              |
| Infrastructure    | GitHub Actions, Docker (planned), Cloud Run      |

---


---

## 🌍 Impact Projections

PrepSense is designed not just to make meal planning easier but to drive measurable sustainability and cost-saving outcomes.

**Estimated per Household Impact** (based on pilot data & market research):
- **5% lower food waste per household**
- ~**60 lbs** of food saved annually through pantry-based planning and expiry alerts
- **$1,250 saved per year** (~75 meals rescued)
- ~**120 kg of CO₂ emissions prevented**

These figures compound significantly as PrepSense adoption grows. For example, with **10,000 active households**:
- **600,000 lbs** of food saved
- **$12.5 million** in total savings
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
cd ios-app
npm install
npx expo start
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

Gratitude to:
- University of Chicago MSADS Faculty
- OpenAI (GPT-4o, Vision API)
- RTS Food Waste Research
- Expo/React Native Community
- The CrewAI Project

---

**PrepSense empowers people to waste less, eat better, and live healthier, turning everyday meal preparation into a sustainable and health-conscious habit**

---

