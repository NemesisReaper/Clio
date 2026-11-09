FROM python:3.11-slim

# System dependencies for PyMuPDF, OpenCV, and fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libgl1 \
    libglib2.0-0 \
    fonts-dejavu-core \
    fonts-indic \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency specifications
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and configuration
COPY clio/ ./clio/
COPY pyproject.toml pytest.ini ./

# Create data directories
RUN mkdir -p /app/data/pdfs /app/data/pages /app/data/crops

ENV PYTHONPATH=/app
ENV ENVIRONMENT=production
ENV DEBUG=false

EXPOSE 8000

CMD ["uvicorn", "clio.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

