FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
# Install redis client so we can subscribe to AI-AIDERS events
RUN pip install --no-cache-dir -r requirements.txt redis pytest

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
