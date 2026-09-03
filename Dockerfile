FROM python:3.12-slim
WORKDIR /app
COPY src/backend/requirements.txt ./src/backend/requirements.txt
RUN pip install --no-cache-dir -r src/backend/requirements.txt
COPY src/ ./src/
WORKDIR /app/src/backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
