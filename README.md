# PrepSense
Capstone project for University of Chicago 

/backend-gateway
    ├── app.py                # Main FastAPI app (entry point)
    ├── routers/              # Directory for route handlers
    │   ├── images.py         # Routes for image upload and processing
    │   ├── pantry.py         # Routes for pantry CRUD operations
    │   ├── recipes.py        # Routes for recipe suggestions
    ├── services/             # Directory for core business logic
    │   ├── vision_service.py # Logic for calling OpenAI Vision API or CV microservice
    │   ├── pantry_service.py # Logic for pantry database operations
    │   ├── recipe_service.py # Logic for recipe generation
    ├── models.py             # Pydantic models for request/response validation
    ├── database.py           # Database connection and setup
    ├── pubsub.py             # Pub/Sub integration (if asynchronous processing is used)
    ├── requirements.txt      # Python dependencies
    ├── .env                  # Environment variables (e.g., VISION_URL, DB credentials)


## Prerequisites

Before you begin, ensure you have the following installed:
- Git
- Python 3.8+
- Node.js (LTS version recommended) and npm (comes with Node.js)
- Expo CLI (you can install it globally via `npm install -g expo-cli` or use `npx` for commands)

## Quick Start

To start the backend or iOS app, use the following commands from the project root:

```bash
# Start the FastAPI backend server (runs on port 8001)
python run_server.py

# Start the iOS app
python run_ios.py
```

## Getting Started

Follow these steps to set up the project environment.

### 1. Backend Setup (`backend-gateway`)

These steps will guide you through setting up the backend service. The Python virtual environment (`venv`) will be created and activated from the project root (`PrepSense`).

#### a. Create and activate a virtual environment (from the `PrepSense` root directory):
It's recommended to use a virtual environment to manage Python dependencies.
```bash
python3 -m venv venv
source venv/bin/activate
```

#### b. Install dependencies:
```bash
pip install -r requirements.txt
```

#### c. Set up environment variables:
- Create a `.env` file in the `backend-gateway` directory.
- Add the required variables (e.g., `VISION_URL`, `OPENAI_API_KEY`):
```bash
VISION_URL=http://localhost:8001/detect
OPENAI_API_KEY=your_openai_api_key
```

#### d. Run the FastAPI app:
```bash
python run_server.py
```

The backend will be available at `http://127.0.0.1:8001`.

### 2. iOS App Setup

#### a. Install dependencies:
```bash
cd ios-app
npm install
```

#### b. Start the app:
```bash
# From the project root
python run_ios.py
```

The app will start and provide a QR code that you can scan with the Expo Go app on your iOS device.

## Collaboration Guidelines

### Branch Management
1. **Main Branch (`main`)**
   - This is the production-ready branch
   - Never commit directly to `main`
   - All changes must come through pull requests

2. **Feature Branches**
   - Create a new branch for each feature/fix
   - Branch naming convention: `feature/feature-name` or `fix/issue-name`
   - Example: `feature/loading-screen`, `fix/auth-bug`

3. **Development Workflow**
   ```bash
   # 1. Always start from an up-to-date main branch
   git checkout main
   git pull origin main

   # 2. Create and switch to your feature branch
   git checkout -b feature/your-feature-name

   # 3. Make your changes and commit them
   git add .
   git commit -m "feat: your descriptive commit message"

   # 4. Push your branch to remote
   git push -u origin feature/your-feature-name

   # 5. Create a pull request on GitHub
   # 6. After review and approval, merge into main
   ```

### Commit Message Guidelines
- Use clear, descriptive messages
- Start with a type: `feat:`, `fix:`, `docs:`, `style:`, `refactor:`, `test:`, `chore:`
- Example: `feat: add loading screen with facts`

### Code Review Process
1. Create a pull request for your changes
2. Request review from at least one team member
3. Address any feedback or requested changes
4. Once approved, merge into main

### Environment Setup
1. **Virtual Environment**
   - Always use the virtual environment
   - Activate it using: `source venv/bin/activate`
   - Keep `requirements.txt` updated
   - Document any new dependencies

2. **Backend Setup**
   - Navigate to project root directory
   - Run: `python run_server.py`
   - Server will be available at `http://127.0.0.1:8001`

3. **iOS App Setup**
   - Navigate to project root directory
   - Run: `python run_ios.py`
   - Use Expo Go app to test on your device

4. **Security**
   - Never commit sensitive data or API keys
   - Keep `.env` files local and in `.gitignore`

### Best Practices
1. **Code Organization**
   - Keep related files together
   - Follow the existing project structure
   - Document new components or functions

2. **Testing**
   - Write tests for new features
   - Ensure all tests pass before merging

3. **Documentation**
   - Update README for significant changes
   - Document API changes
   - Add comments for complex logic

4. **Regular Updates**
   - Pull from main regularly to stay up to date
   - Resolve conflicts early
   - Keep your feature branch current

### Getting Help
- Check existing documentation first
- Ask in team chat for quick questions
- Schedule a meeting for complex issues
- Document solutions for future reference

