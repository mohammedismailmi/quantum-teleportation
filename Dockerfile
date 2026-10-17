# Multi-stage Dockerfile for Quantum Teleportation Full-Stack App
# Stage 1: Build the React frontend
FROM node:20-slim AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./
RUN npm run build

# Stage 2: Python FastAPI backend with Qiskit
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies including libgomp for OpenMP support
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and compiled frontend
COPY . .
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Ensure entrypoint script is executable
RUN chmod +x ./entrypoint.sh

# Expose default port
EXPOSE 8000
ENV PORT=8000

# Run FastAPI server via entrypoint script
CMD ["./entrypoint.sh"]
