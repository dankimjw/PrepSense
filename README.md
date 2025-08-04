# 🥦 PrepSense — Make Every Ingredient Count

**Smart pantry insights + recipe generation to reduce food waste, improve nutrition, and save money—all powered by AI.**

---

## 📋 Table of Contents

1. [About PrepSense](#about-prepsense)  
2. [Problem & Motivation](#problem--motivation)  
3. [Features & Highlights](#features--highlights)  
4. [System Architecture & Workflow](#system-architecture--workflow)  
5. [Tech Stack & Tools Used](#tech-stack--tools-used)  
6. [Getting Started](#getting-started)  
7. [Usage Examples & Screenshots](#usage-examples--screenshots)  
8. [Project Structure](#project-structure)  
9. [Roadmap & Future Features](#roadmap--future-features)  
10. [Known Issues & Troubleshooting](#known-issues--troubleshooting)  
11. [FAQ](#faq)  
12. [Contributing & Development Workflow](#contributing--development-workflow)  
13. [License](#license)  
14. [Credits & Acknowledgements](#credits--acknowledgements)  
15. [Contact & Support](#contact--support)  

---

## 1. About PrepSense

PrepSense combines multimodal AI vision with structured agent-based logic to help users scan their pantry, detect expiring ingredients, and generate healthy recipes tailored to what's already in stock. It’s designed to minimize food waste, improve nutritional intake, and simplify meal planning.

---

## 2. Problem & Motivation

- **Global food waste**: ~60M tons wasted in the U.S. annually—billions of dollars lost and millions of meals thrown away.  
- **Neglected perishables**: Items spoil because users lose track of what they’ve bought.  
- **Diet inefficiency**: People often lack insight into nutritional balance based on food at hand.

PrepSense tackles these by automating pantry management, highlighting at-risk items, and recommending balanced meals using available ingredients.

---

## 3. Features & Highlights

- 📷 **AI-powered pantry ingestion**: Scan receipts or fridge photos to auto-populate structured pantry entries with expiry dates.  
- 🍽️ **Smart recipe generation**: Chat-based customization, health-conscious suggestions, and filtering (e.g., low sugar, vegetarian, quick-prep).  
- 🧮 **Nutrition breakdown & ranking score**: Macros and health index for each dish.  
- 🛒 **Missing-item alerts**: Add needed ingredients to a shopping list seamlessly.  
- 🤖 **Modular agent pipeline**: BiteCam, Scanner Sage, Fresh Filter, NutriCheck, HealthRanker, ChefParser, JudgeThyme, and RecipeRover each handle specialized stages.

---

## 4. System Architecture & Workflow

```
[ Mobile App (React Native / Expo) ]
             ↕
    [ Backend API (FastAPI) ]
             ↕
      [ Agentic Processing Pipeline ]
             ↕
        [ Pantry Database (SQLite/PostgreSQL) ]
             ↕
   [ LLM + Computer Vision APIs (e.g. GPT‑4o, Vision API) ]
```

Agents coordinate to ingest image data, process with chain-of-thought multi-modal LLMs, evaluate recipe feasibility, and output user-friendly recipe suggestions.

---

## 5. Tech Stack & Tools Used

| Layer               | Technology                            |
|---------------------|----------------------------------------|
| Mobile App          | React Native / Expo                   |
| Backend API         | Python, FastAPI            |
| Computer Vision / OCR | OpenAI GPT‑4o Vision API, Tesseract |
| Agent Workflow      | CrewAI|
| Database            | SQLite (dev), PostgreSQL (production) |
| Dev Tools           | Docker, GitHub Actions, Cloud Run |

---

## 6. Getting Started

### 🔧 Prerequisites

- Python 3.10+  
- Node.js & npm  
- Expo CLI (`npm install -g expo-cli`)  
- `.env` file for API keys

### 🛠 Installation

```bash
git clone https://github.com/dankimjw/PrepSense.git
cd PrepSense

# Backend
pip install -r requirements.txt

# Frontend
cd app
npm install
```

### ⚙️ Configuration

Create `.env` in project root:

```env
OPENAI_API_KEY=your_openai_key
VISION_API_KEY=your_vision_api_key
DATABASE_URL=sqlite:///./db.sqlite3
```

### 🚀 Running Locally

```bash
# Start backend
uvicorn backend.main:app --reload

# Launch mobile client
cd app
npx expo start
```

---

## 7. Usage Examples & Screenshots

### 1. Pantry Ingestion  
Upload a photo or receipt → Pantry items auto-detected and displayed  
*Insert visual screenshot once available*

### 2. Recipe Chat Flow  
“Suggest 3 lunch recipes using only items in pantry and avoid dairy.”  
*Show chat window screenshot here*

### 3. Health Scoring  
Recipes ranked by nutritional density and balanced macros  
*Insert health score screenshot*

---

## 8. Project Structure

```
/
├── backend/
│   ├── api/
│   ├── agents/
│   ├── models.py
│   └── utils/
├── app/                # Mobile frontend (React Native)
├── .env.example
├── requirements.txt
├── README.md
└── LICENSE
```

---

## 9. Roadmap & Future Features

- Plugin-based recipe sources (e.g., dietary filters, cuisines) ✅  
- Grocery/shopping list integration 📦  
- Community sharing & meal rating features  
- Docker-based deployment for production  
- Automated testing & CI/CD pipelines  
- Support for family/personal user profiles

---

## 10. Known Issues & Troubleshooting

- 📌 OCR accuracy depends on image clarity—consider standard lighting/preprocessing  
- 🧪 Recipe suggestions might occasionally include rarely used pantry items—manual filtering may be needed  
- ⚠️ Ensure `.env` contains proper API keys or startup will fail  
- Test suite coverage still under development—manual checks encouraged

---

## 11. FAQ

**Q: Can I run PrepSense without OpenAI access?**  
**A:** Not fully; backend features require valid GPT‑4o and Vision API tokens.

**Q: How frequently does it update pantry expiry?**  
**A:** Each ingest or request triggers a new scan and updates state—no automatic polling yet.

---

## 12. Contributing & Development Workflow

1. Fork the repo  
2. Create feature branch: `git checkout -b feature/xyz`  
3. Write code and add tests if applicable  
4. Format code using `black`, lint with `flake8`  
5. Open a Pull Request for review

---

## 13. License

This project is licensed under the **MIT License**—see the [LICENSE](LICENSE) file for details.

---

## 14. Credits & Acknowledgements

- University of Chicago MS in Applied Data Science Capstone Project  
- OpenAI GPT‑4o & Vision API  
- Expo framework & React Native team  
- Food waste stats from RTS report on Food Waste in America  


---

## 15. Contact & Support

💬 For questions or discussion, raise an **Issue** or **Pull Request**.  
📧 Project Maintainers:  
- Daniel Kim (@dankimjw)  
- Akash Sannidhanam  
- Bonny Mathew  
- Prahalad Ravi

---

We welcome your feedback, bug reports, and contributions. Let’s work together to build a smarter, more sustainable future—one ingredient at a time. 🌱
