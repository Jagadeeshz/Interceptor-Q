FROM python:3.11-slim

WORKDIR /app

# Copy the hermes package into /app/hermes
COPY . /app/hermes/

# Set environment variables
ENV PYTHONPATH=/app

# Install dependencies
RUN pip install --no-cache-dir -r /app/hermes/requirements.txt

EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "hermes.__init__:app", "--host", "0.0.0.0", "--port", "8000"]