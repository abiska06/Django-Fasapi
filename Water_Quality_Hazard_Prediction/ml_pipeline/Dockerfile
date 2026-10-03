FROM python:3.12-slim

WORKDIR /app

# System deps: scikit-learn/scipy wheels need a C toolchain on some platforms
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8001

CMD ["uvicorn", "fastapi_service:app", "--host", "0.0.0.0", "--port", "8001"]
