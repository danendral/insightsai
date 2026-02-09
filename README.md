# InsightsAI

AI-powered sales & marketing analytics platform. Upload CSV data, visualize trends, and ask questions in natural language.

## Features

- **CSV Upload** — Upload your own sales/marketing data or use the built-in sample dataset
- **Auto-generated Charts** — Revenue trends, category breakdowns, campaign performance, marketing ROI
- **Natural Language Queries** — Ask questions like "What was the best performing month?" and get AI-powered answers
- **KPI Dashboard** — Key metrics at a glance: revenue, customers, conversion rates, leads

## Tech Stack

### Backend
- **FastAPI** — Modern Python web framework with automatic API docs, type validation, and async support
- **pandas** — Data processing and analysis
- **Anthropic Claude API** — Powers the natural language query feature

### Frontend
- **React** (via Vite) — Component-based UI library
- **Tailwind CSS v4** — Utility-first CSS framework
- **Recharts** — React-native charting library
- **Lucide React** — Icon library

## Project Structure

```
insightsai/
├── backend/
│   ├── main.py              # FastAPI application with all endpoints
│   ├── requirements.txt     # Python dependencies
│   ├── .env.example         # Environment variable template
│   ├── sample_data/
│   │   └── sales_data.csv   # Built-in sample dataset
│   └── uploads/             # User-uploaded CSV files
├── frontend/
│   ├── src/
│   │   ├── main.jsx         # React entry point
│   │   ├── App.jsx          # Root component (state management)
│   │   ├── components/
│   │   │   ├── Header.jsx      # App header
│   │   │   ├── DataLoader.jsx  # CSV upload / sample data loader
│   │   │   ├── Dashboard.jsx   # Charts and KPI cards
│   │   │   └── QueryPanel.jsx  # Natural language query interface
│   │   └── lib/
│   │       ├── api.js       # API client (all backend communication)
│   │       └── utils.js     # Tailwind class merge utility
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── .gitignore
└── README.md
```

## Setup & Run Locally

### Prerequisites
- Python 3.10+
- Node.js 18+
- An [Anthropic API key](https://console.anthropic.com/) (for the AI query feature)

### 1. Backend

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set up your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

The API will be running at http://localhost:8000. Visit http://localhost:8000/docs for interactive API documentation.

### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be running at http://localhost:5173.

### 3. Use the App

1. Open http://localhost:5173 in your browser
2. Click **Load Sample Data** (or upload your own CSV)
3. Explore the dashboard charts
4. Switch to the **AI Insights** tab to ask questions about your data

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/sample` | Load the built-in sample dataset |
| `POST` | `/api/upload` | Upload a CSV file |
| `GET` | `/api/data` | Get dataset summary statistics |
| `GET` | `/api/data/raw` | Get paginated raw data rows |
| `GET` | `/api/charts/{type}` | Get chart data (`revenue-trend`, `by-category`, `by-region`, `campaign-performance`, `marketing-roi`) |
| `POST` | `/api/query` | Ask a natural language question |

## Sample Data

The included dataset contains 12 months of sales & marketing data across 3 product categories (Software, Consulting, Hardware) and 3 regions (North America, Europe, Asia Pacific), with metrics including:

- Revenue, customer count, new customers
- Conversion rates, marketing spend, leads generated
- Deals closed, average deal size, campaign names, churn rate
