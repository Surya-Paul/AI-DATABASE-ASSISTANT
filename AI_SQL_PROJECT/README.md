# AI SQL Assistant

A mini "ChatGPT for databases" web application that converts natural language questions into executable SQL queries, runs them against a local SQLite database, and provides tools to explain, optimize, and auto-correct queries.

## Tech Stack
- **Backend**: Python, FastAPI, SQLAlchemy, Anthropic Claude API
- **Frontend**: React, Vite, Vanilla CSS (Dark Mode / Glassmorphism)
- **Database**: SQLite (local)

## Features
- **Natural Language to SQL**: Converts plain English into SQL queries.
- **SQL Execution**: Executes queries safely and displays the result in a table.
- **SQL Explanation**: Clause-by-clause explanation of the generated SQL in plain English.
- **SQL Optimization**: Provides optimization suggestions based on the SQLite `EXPLAIN QUERY PLAN`.
- **Query Correction**: Auto-corrects SQL if the execution fails due to syntax or database errors.
- **Destructive Query Protection**: Prompts for user confirmation before executing INSERT, UPDATE, DELETE, DROP, or ALTER statements.

## Setup Instructions

### Prerequisites
- Python 3.9+
- Node.js 18+
- Anthropic API Key (`ANTHROPIC_API_KEY`)

### 1. Backend Setup

1. Navigate to the `backend` directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure the environment variables:
   - Edit the `.env` file in the `backend` directory.
   - Add your Anthropic API key: `ANTHROPIC_API_KEY=your_api_key_here`

5. Seed the database with sample data:
   ```bash
   python seed.py
   ```
   *This creates `data.db` and populates the `Employee` table with 20 sample rows.*

6. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
   *The backend will be running at `http://localhost:8000`.*

### 2. Frontend Setup

1. Open a new terminal and navigate to the `frontend` directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   *The frontend will typically run at `http://localhost:5173`. Open this URL in your browser.*

## Usage Examples
- "Show the five highest-paid employees"
- "How many employees are in the Engineering department?"
- "What is the average salary in the Sales department?"
- "Delete all employees in HR" *(this will trigger the destructive query confirmation)*
