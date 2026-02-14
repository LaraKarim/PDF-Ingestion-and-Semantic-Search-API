
FROM python:3.10-slim

WORKDIR /app


ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Upgrade pip to avoid transitive hash mismatches 
RUN pip install --no-cache-dir --upgrade pip

# Install PyTorch CPU first to avoid downloading the GPU larger version
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install grpcio first so chromadb's (hashed) dependency is satisfied by current PyPI wheel
RUN pip install --no-cache-dir "grpcio>=1.58.0"

# Install remaining dependencies
COPY dependencies.txt .
RUN pip install --no-cache-dir -r dependencies.txt

# Application code
COPY . .

# Expose API port
EXPOSE 8000

# Run FastAPI with uvicorn; log to stdout for Docker
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
