# NOTE: This Dockerfile must be built with the project root directory as the context.
# Build command: docker build -t initresume-api -f api/Dockerfile .
#
FROM python:3.11-slim

# Prevent writing pyc files and buffering stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies (build-essential, git, curl, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser engines and system dependencies
RUN playwright install --with-deps chromium

# Copy application files
COPY . /app/

# Expose API port
EXPOSE 8000

# Default command to run FastAPI development server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
