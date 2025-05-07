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


## Starting the iOS App
To start the app, cd to ios-app folder and enter in the terminal `npx expo start --clear --localhost`

## Working on the project

### 1. Clone the Repository
Run the following command to clone the repository:
```bash
git clone https://github.com/<your-username>/PrepSense.git
cd PrepSense
```
### 2. Backend Setup (`backend-gateway`)

#### a. Navigate to the `backend-gateway` directory:
```bash
cd backend-gateway
```

#### b. Create and activate a virtual environment:
```ash
python3 -m venv venv
source venv/bin/activate
```

#### c. Install Python dependencies:
```bash
pip install -r requirements.txt
```

#### d. Set up environment variables:
- Create a `.env` file in the `backend-gateway` directory.
- Add the required variables (e.g., `VISION_URL`, `OPENAI_API_KEY`):
```bash
VISION_URL=http://localhost:8001/detect
OPENAI_API_KEY=your_openai_api_key
```

#### e. Run the FastAPI app:
```bash
uvicorn app:app --reload
```

The backend will be available at `http://127.0.0.1:8000`.


