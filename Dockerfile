# 1. Use official Python image as base
FROM python:3.12-slim

# 2. Set working directory
WORKDIR /app

# 3. Copy only requirements.txt and install early to leverage Docker layer caching
COPY requirements.txt .

# 4. Install system dependencies (for pytesseract + faiss + OCR)
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 5. Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 6. Copy all app files
COPY . .

# 7. Expose port (FastAPI default)
EXPOSE 8000

# 8. Set environment variables (optional)
ENV PYTHONUNBUFFERED=1

# 9. Start the app (adjust main filename as needed)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
