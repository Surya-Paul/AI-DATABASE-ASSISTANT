# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (for Docker layer caching)
COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy the full application
COPY backend/ /app/backend/
COPY frontend/ /app/frontend/

# Seed the database at build time so it's ready to go
WORKDIR /app/backend
RUN python seed.py

# Expose only one port — FastAPI serves both API and frontend
EXPOSE 8000

# Run Uvicorn in production mode
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
