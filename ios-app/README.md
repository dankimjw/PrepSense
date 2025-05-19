# PrepSense

> **Capstone Project · University of Chicago · Spring 2025**
> *Track what’s in your pantry, reduce food waste, and discover recipes powered by AI & computer vision.*

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)

   1. [Prerequisites](#prerequisites)
   2. [Quick Start](#quick-start)
   3. [Backend Setup](#backend-setup)
   4. [iOS (App) Setup](#ios-app-setup)
5. [Environment Variables](#environment-variables)
6. [Project Structure](#project-structure)
7. [Collaboration Workflow](#collaboration-workflow)
8. [Commit Conventions](#commit-conventions)
9. [Best Practices](#best-practices)
10. [License](#license)

---

## Project Overview

PrepSense combines **FastAPI**, **OpenAI Vision**, and **Expo React Native** to let users:

* 📸 **Snap a photo** of groceries to auto‑detect items, quantity, and expiry dates.
* 🥫 **Maintain a smart pantry** with CRUD operations (add, edit, consume, delete).
* 🍽️ **Generate recipe ideas** tailored to current inventory and dietary preferences.
* 🔔 **Get notifications** before food expires to minimize waste.

## Architecture

```mermaid
flowchart TD
    subgraph Mobile (Expo App)
        A1[Camera / Gallery]
        A2[Pantry Dashboard]
        A3[Recipe Suggestions]
        A1 -->|REST| B(API Gateway)
        A2 -->|REST| B
        A3 -->|REST| B
    end

    subgraph Backend (FastAPI)
        B(API Gateway) --> C1(Vision Service)
        B --> C2(Pantry Service)
        B --> C3(Recipe Service)
    end

    C2 -->|SQLAlchemy| D[(PostgreSQL DB)]
    C1 -->|HTTP| E(OpenAI Vision or CV Microservice)
```

*For asynchronous processing heavy workloads, a Pub/Sub layer (e.g., Redis Streams) can be enabled between the API Gateway and the Vision Service.*

## Tech Stack

| Layer        | Technology                                      |
| ------------ | ----------------------------------------------- |
| Mobile (iOS) | Expo React Native, TypeScript, React Navigation |
| Backend      | FastAPI, Pydantic, Uvicorn                      |
| AI Services  | OpenAI Vision API / custom CV model             |
| Data         | PostgreSQL, SQLAlchemy                          |
| Dev Ops      | GitHub Actions (CI), Docker (optional)          |

## Getting Started

### Prerequisites

* **Git**
* **Python 3.8+**
* **Node.js (LTS)** & **npm** (bundled)
  `npm install -g expo-cli` (optional, or use `npx`)

### Quick Start

Clone the repository, install both Python and Node dependencies, then launch the backend and mobile app:

```bash
# 0. Clone & enter the project root
git clone https://github.com/<your-org>/PrepSense.git
cd PrepSense

# 1. Set up Python virtual environment & backend dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r backend-gateway/requirements.txt

# 2. Ensure Node.js LTS is installed, then grab Expo app packages
cd ios-app
npm install
cd ..

# 3. Start the FastAPI backend (http://127.0.0.1:8001)
python run_server.py

# 4. Start the Expo app (shows a QR code for Expo Go)
python run_ios.py
```

Scan the QR code printed in the terminal with **Expo Go** on your iOS device to load the app.

---

## Backend Setup

> All commands below assume you are inside the project root.

1. **Create & activate a virtual env**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. **Install dependencies**

   ```bash
   pip install -r backend-gateway/requirements.txt
   ```
3. **Configure environment variables** (see [Environment Variables](#environment-variables)).
4. **Run the server**

   ```bash
   python run_server.py  # alias for: uvicorn backend-gateway.app:app --reload --port 8001
   ```

## iOS (App) Setup

1. ```bash
   cd ios-app
   npm install
   ```
2. ```bash
   npm start           # or: npx expo start --tunnel
   ```
3. Install **Expo Go** on your device and scan the QR code.

---

## Environment Variables

Create a `.env` file in `backend-gateway/` with:

```
# OpenAI Vision endpoint (or CV microservice URL)
VISION_URL=http://localhost:8001/detect

# Your OpenAI API key
OPENAI_API_KEY=sk-...

# Database connection URL
DATABASE_URL=postgresql://user:password@localhost:5432/prepsense
```

> **Do not** commit `.env` files—`gitignore` already excludes them.

---

## Project Structure

```text
PrepSense/
├── backend-gateway/
│   ├── app.py               # FastAPI entry point
│   ├── routers/
│   │   ├── images.py        # /images endpoints
│   │   ├── pantry.py        # /pantry endpoints
│   │   └── recipes.py       # /recipes endpoints
│   ├── services/
│   │   ├── vision_service.py
│   │   ├── pantry_service.py
│   │   └── recipe_service.py
│   ├── models.py            # Pydantic schemas
│   ├── database.py          # SQLAlchemy engine & metadata
│   ├── pubsub.py            # Optional async messaging
│   ├── requirements.txt
│   └── .env.example         # Sample env vars
├── ios-app/                 # Expo React Native source
│   ├── App.tsx
│   ├── package.json
│   └── ...
├── run_server.py            # Helper script to start backend
├── run_ios.py               # Helper script to start Expo
└── README.md
```

---

## Collaboration Workflow

1. **Main (`main`)** is always deployable—never commit directly.
2. **Feature branches** use the pattern `<your_name>-<feature>` (e.g., `daniel-loading-screen`) or `<your_name>-<fix>` for bug fixes (e.g., `daniel-auth-bug`).
3. Open a **pull request** → request at least **1 review** → squash‑merge.
4. Keep your branch up‑to‑date with `main` to minimize conflicts.

### Example Workflow

```bash
git checkout main && git pull

git checkout -b yourname-vision-batch-upload
# code...

git add .
git commit -m "feat: support batch image upload"
git push -u origin yourname-vision-batch-upload
# open PR on GitHub
```

## Commit Conventions

| Type         | When to use                                             | Example                                   |
| ------------ | ------------------------------------------------------- | ----------------------------------------- |
| **feat**     | New feature                                             | `feat: add expiry‑date detector`          |
| **fix**      | Bug fix                                                 | `fix: correct SQL timezone handling`      |
| **docs**     | Documentation                                           | `docs: clarify env vars`                  |
| **refactor** | Code change that neither fixes a bug nor adds a feature | `refactor: extract recipe engine`         |
| **test**     | Adding or updating tests                                | `test: add unit tests for pantry service` |
| **chore**    | Build tasks, dependencies                               | `chore: bump FastAPI to 0.110`            |

---

## Best Practices

* **Virtual env:** always activate (`source venv/bin/activate`).
* **Secrets:** keep keys in `.env` (never in code or commits).
* **Testing:** write tests for new logic; run `pytest` locally & in CI.
* **Linting:** we use **ruff** & **black**; `pre-commit` hooks run automatically.
* **Docs:** update this README + inline docstrings for complex functions.

## License

Distributed under the MIT License. See `LICENSE` for details.
