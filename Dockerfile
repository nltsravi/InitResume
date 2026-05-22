# Use official Python runtime as a parent image
FROM python:3.11-slim

# Install system dependencies required for running Playwright and other tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file first to leverage Docker cache
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers and their system dependencies inside the container
RUN playwright install --with-deps chromium

# Copy the rest of the application code
COPY . .

# Expose ports (FastAPI runs on 8000)
EXPOSE 8000
