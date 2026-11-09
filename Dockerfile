FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend /app/backend
COPY database /app/database
COPY frontend /app/frontend
RUN mkdir -p /app/uploads
EXPOSE 5000
CMD ["sh", "-c", "if [ \"${DEMO_SEED:-1}\" = 1 ]; then python database/seed.py; fi; exec python backend/app.py"]
