FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Create data directories that might not persist in production
RUN mkdir -p data/arquivos_enviados data

# Set environment to production-like
ENV PYTHONUNBUFFERED=1
ENV PORT=8501

# Run the application using the same script as Railway
CMD ["bash", "start.sh"]