FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-bookworm AS application

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY scripts/docker-start.sh ./docker-start.sh
RUN chmod +x docker-start.sh
COPY --from=frontend-build /frontend/dist ./app/static

ENV PORT=8080
ENV DEBUG=false
ENV SEED_DEMO_DATA=true
ENV LIGHTWEIGHT_PREDICTIONS=true
ENV JWT_SECRET=a8f3c2e91b047d6e5f0a9c3b8d7e4f1c6a2b9d0e8f7c4a1b6d3e9f2c5a8b1d4e7f0

EXPOSE 8080

CMD ["./docker-start.sh"]
