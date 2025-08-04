# 🥦 PrepSense — Make Every Ingredient Count

**Capstone Project — University of Chicago MS in Applied Data Science (2025)**  
**Team:** Akash Sannidhanam, Daniel Kim, Bonny Mathew, Prahalad Ravi

---

## 🧭 Executive Summary

In today’s fast-paced world, consumers are increasingly making conscious choices about health, sustainability, and waste reduction. However, they often lack the tools to effectively manage their kitchen inventory and meal planning in a way that aligns with these values. PrepSense was created to solve this gap.

**PrepSense** is a mobile-first, AI-powered pantry and recipe assistant that empowers users to manage their food intelligently—from inventory tracking to personalized meal recommendations. Built as a capstone project for the University of Chicago’s MS in Applied Data Science program, PrepSense combines computer vision, CrewAI-powered agent orchestration, and personalized large language models (LLMs) to transform everyday household decisions into impactful actions.

The system works by allowing users to scan their pantry or receipts, automatically detecting items, quantities, and expiry dates. From there, it generates customized recipes based on what’s on hand, dietary restrictions, and personal preferences—minimizing waste while maximizing nutrition. Users are also given insight into nutritional content, missing items for recipes, and the ability to build a dynamic shopping list. This seamless end-to-end experience is enabled by a team of modular AI agents working in coordination through the CrewAI framework.

With food waste costing the U.S. over **$218 billion annually**, PrepSense represents not just a technological innovation—but a real opportunity to drive meaningful change at scale. At just 10,000 users, PrepSense could help rescue over 30,000 meals per month, reduce more than 100 tons of food waste, and deliver collective savings of over $1M annually.

PrepSense isn’t just a pantry tool—it’s a sustainability ally, a nutrition guide, and a smart kitchen companion.

---

## 💡 Problem

Each year, the U.S. wastes over **60 million tons** of food—enough to feed **120 million people** and costing **$218 billion**. Much of this waste happens in everyday homes due to:
- Forgotten or expired items
- Poor visibility into pantry contents
- Last-minute decisions and unbalanced meals

Consumers need a smarter way to manage their food and plan their meals.

---

## 🎯 Business Objective

**PrepSense** was designed to:
- 🧠 Provide visibility into pantry contents through computer vision
- ⏰ Surface at-risk items before they expire
- 🍽 Suggest recipes that optimize health, taste, and sustainability
- 📈 Quantify household impact: food saved, money saved, carbon reduced

---

## 🧑‍💼 Target User: Lily

- Age: 30 | Location: Dallas, TX  
- Busy professional, prefers cooking at home  
- Cares about sustainability but forgets what she has at home  
- “I always buy with good intentions... but end up wasting food.”

PrepSense helps Lily make better use of what she already has—easily, intuitively, and intelligently.

---

## 📲 Product Overview

> _“From photo to plate, all within one app.”_

### 🔍 Pantry Tracking
- Upload photo of fridge or receipt
- Detect item name, brand, quantity, and expiry date
- Color-coded, editable inventory

**[Insert Pantry UI Screenshot]**

### 🍽 Recipe Assistant
- Chat-based interface for customized meal ideas
- Personalization using saved preferences
- Suggests healthy options using pantry-first approach
- Integrates nutritional stats and health ranking

**[Insert Recipe Chat Screenshot]**

### 🛒 Shopping Companion
- Detect missing ingredients for suggested recipes
- Add to shopping list (future: link with grocery APIs)
- Optional integration with user dietary restrictions

**[Insert Shopping Cart Screenshot]**

---

## 🧠 AI Architecture with CrewAI

PrepSense uses [**CrewAI**](https://github.com/joaomdmoura/crewai) for orchestrating a team of specialized AI agents, each responsible for one stage in the flow.

| Agent           | Function                                                                 |
|------------------|--------------------------------------------------------------------------|
| **BiteCam**        | Captures and processes pantry images                                     |
| **Scanner Sage**   | Converts images to structured JSON via multimodal LLM pipeline          |
| **Fresh Filter**   | Flags expired or unusable ingredients                                   |
| **NutriCheck**     | Calculates macros, nutrition balance, dietary scores                   |
| **HealthRanker**   | Ranks recipes based on user preferences + health impact                |
| **ChefParser**     | Converts LLM output into clean user-facing recipe format               |
| **JudgeThyme**     | Validates feasibility (matches pantry + preferences)                   |
| **RecipeRover**    | Selects final recipe recommendation                                    |

CrewAI enables modular, scalable, and memory-capable orchestration between agents.

**[Insert CrewAI Pipeline Diagram]**

---

## ⚙️ Technical Stack

| Layer           | Technology                             |
|------------------|-----------------------------------------|
| Frontend         | React Native, Expo                     |
| Backend API      | Python, FastAPI                        |
| Vision Pipeline  | OpenAI Vision API, Image Preprocessing |
| LLM Reasoning    | GPT-4o with Chain-of-Thought Prompting |
| Orchestration    | CrewAI                                 |
| Database         | SQLite (dev), PostgreSQL (prod-ready)  |
| Infrastructure   | Docker, GitHub Actions (CI/CD), Cloud Run |

---

## 📈 Measurable Impact (Projected @ 10,000 users)

| Metric                | Value                      |
|------------------------|----------------------------|
| Meals Rescued          | 30,000+ per month          |
| Food Saved             | 100+ tons per month        |
| Grocery Waste Savings  | $1M+ annually              |
| CO₂ Offset             | 200+ tons per year         |
| Health Score Lift      | +25% average improvement   |

**[Insert Household Impact Infographic]**

---

## 🚀 Setup & Deployment

```bash
git clone https://github.com/dankimjw/PrepSense.git
cd PrepSense

# Backend
pip install -r requirements.txt

# Frontend
cd app
npm install
npx expo start
```

**.env Example**
```env
OPENAI_API_KEY=your_openai_key
VISION_API_KEY=your_vision_key
DATABASE_URL=sqlite:///./pantry.db
```

---

## 🛣 Roadmap

- 🛍 Grocery API integration (e.g., Instacart, Amazon Fresh)
- 👪 Family account support & shared pantry views
- 🖼 Visual recipe previews from LLM output
- 📈 Personal dashboard for food, waste, health impact
- 🌍 Multilingual and cultural recipe support

---

## 📚 Lessons Learned

- Vision+LLM accuracy improves dramatically with chain-of-thought prompting
- Agent orchestration (via CrewAI) helps decouple logic and simplify testing
- Users appreciate transparency—nutritional scores improved engagement

---

## 👥 Team

- **Akash Sannidhanam**  
- **Daniel Kim**  
- **Bonny Mathew** 
- **Prahalad Ravi** 

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgements

- University of Chicago MSADS Program  
- OpenAI (GPT-4o + Vision API)  
- RTS Food Waste Report  
- Expo / React Native ecosystem  
- CrewAI framework

---

**PrepSense makes sustainability simple—one ingredient at a time.**
