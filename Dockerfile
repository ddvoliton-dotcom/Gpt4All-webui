# Multi-stage: build frontend, then runtime image with Python + built frontend
FROM node:18-alpine AS frontend-build
WORKDIR /build-frontend
COPY frontend/ ./frontend/
WORKDIR /build-frontend/frontend
RUN npm ci --silent && npm run build

FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends 
    build-essential curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api
COPY --from=frontend-build /build-frontend/frontend/dist ./frontend/dist

ENV PYTHONUNBUFFERED=1
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn api.stateless_proxy:app --host 0.0.0.0 --port ${PORT} --proxy-headers"]