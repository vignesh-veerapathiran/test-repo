# Use a minimal and secure base image
FROM python:3.9-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    FLASK_APP=app.py \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=8080

# Set working directory
WORKDIR /app

# Copy requirement file and install dependencies securely
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the application port
EXPOSE 8080

# Create and switch to a non-root user
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

# Run the application
CMD ["flask", "run"]