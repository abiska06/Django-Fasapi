FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# The actual code/data is supplied at runtime via the docker-compose volume
# mount (the whole project repo), so COPY here is just a fallback for
# running this image standalone outside compose.
COPY . .

EXPOSE 8888

CMD ["jupyter", "notebook", \
     "--ip=0.0.0.0", "--port=8888", "--no-browser", "--allow-root", \
     "--ServerApp.token=", "--ServerApp.password="]
