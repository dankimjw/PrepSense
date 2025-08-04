
# 🥦 PrepSense

**Make Every Ingredient Count**

PrepSense is a sustainability-driven smart pantry and recipe assistant that helps users reduce food waste, improve nutritional balance, and make the most of what they already have at home.

---

## 🚀 Project Overview

In the U.S. alone, ~60 million tons of food go to waste annually—enough to feed 120 million people and costing $218 billion per year. PrepSense aims to fight this problem by helping users like *Lily* track pantry items, detect product expiry, and generate personalized, healthy recipes using ingredients they already own.

PrepSense combines computer vision, large language models, and agent-based orchestration to create a seamless user experience from pantry management to meal preparation.

---

## 🛠 Features

### 🧠 AI-Powered Pantry Tracking
- Scan receipts or fridge photos to auto-detect items, quantities, and expiry dates
- Multimodal LLM pipeline with chain-of-thought prompting
- JSON output stored in a structured pantry database
- Color-coded inventory with manual editing support

### 🍽️ Smart Recipe Generation
- Recipes matched to pantry items and user preferences
- Chat-based customization (e.g. “healthy breakfast ideas”)
- Nutritional stats and health ranking for each recipe
- Add missing ingredients directly to a shopping cart

### 🧑‍🍳 Agent-Oriented Architecture
- `BiteCam` – Captures pantry via images
- `Scanner Sage` – Reads item data from DB
- `Fresh Filter` – Removes expired or spoiled items
- `NutriCheck` – Evaluates dietary balance
- `HealthRanker` – Scores recipes by health
- `ChefParser` – Converts output to user-friendly format
- `JudgeThyme` – Evaluates recipe feasibility
- `RecipeRover` – Suggests optimal recipes

---

## 📱 Tech Stack

| Component        | Technology                    |
|------------------|-------------------------------|
| Frontend (Mobile)| React Native / Expo           |
| Backend          | Python, FastAPI (or Flask)    |
| AI & CV          | OpenAI GPT-4o, Multimodal Vision API |
| Database         | SQLite / PostgreSQL           |
| Agentic Workflow | LangChain / Custom Orchestration |
| Hosting/Infra    | GitHub / TBD                  |

---

## 🧪 Setup Instructions

> **Note**: Instructions may evolve as the project grows.

1. **Clone the repo**  
```bash
git clone https://github.com/dankimjw/PrepSense.git
cd PrepSense
```

2. **Install dependencies**  
(Example: Python backend)  
```bash
pip install -r requirements.txt
```

3. **Run the app**  
For mobile frontend (Expo):
```bash
cd app
npm install
npx expo start
```

4. **Configure environment variables**  
Create a `.env` file and add any necessary API keys for image processing, OpenAI, etc.

---

## 📊 Impact Potential

At scale (10,000 users), PrepSense could help:
- Save tons of food from landfills
- Rescue 30k+ meals per month
- Cut down $1M+ in grocery waste
- Improve household health metrics
- Lower carbon footprint through sustainable behavior

---

## 👥 Team

- **Akash Sannidhanam**
- **Daniel Kim**
- **Bonny Mathew**
- **Prahalad Ravi**

Built as part of the [University of Chicago MS in Applied Data Science Capstone Project](https://professional.uchicago.edu/find-your-path/graduate-programs/applied-data-science).

---

## 📜 License

[MIT License](LICENSE)

---

## 🙌 Acknowledgements

- RTS: Food Waste in America Report  
- OpenAI for GPT models  
- Expo for mobile framework  
- University of Chicago for guidance and support

---
