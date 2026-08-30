FROM python:3.9-slim
RUN apt-get update && apt-get install -y gdal-bin libgdal-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "core.app:create_app()", "--bind", "0.0.0.0:5000", "--workers", "2"]
