FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app/

# Create virtual environment
RUN python -m venv /app/venv

# Activate virtual environment and install dependencies
ENV VIRTUAL_ENV=/app/venv
ENV PATH="/app/venv/bin:$PATH"

# Upgrade pip and install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Install Playwright and browsers
RUN playwright install chromium

# Expose port
EXPOSE 8000

# Set environment for production
ENV PYTHONUNBUFFERED=1

# Run the API server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]