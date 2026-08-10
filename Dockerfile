FROM node:22-alpine AS frontend-build

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

FROM python:3.12-slim AS application

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app
COPY run.py .
COPY --from=frontend-build /frontend/dist ./app/static

ENV PORT=8080
ENV DEBUG=false
ENV SEED_DEMO_DATA=true
ENV LIGHTWEIGHT_PREDICTIONS=true

EXPOSE 8080

CMD ["python", "run.py"]
