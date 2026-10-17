FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PORT=8000 DATABASE_PATH=/data/northstar.db
WORKDIR /app
COPY server.py index.html styles.css app.js ./
RUN mkdir -p /data && useradd --uid 10001 --no-create-home appuser && chown -R appuser:appuser /app /data
USER appuser
EXPOSE 8000
CMD ["python", "server.py"]

