# Use an official, lightweight Python slim image
FROM python:3.10-slim

# Prevent Python from writing .pyc files to disk and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Set the working directory inside the container
WORKDIR /workspace

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies safely
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Security Best Practice: Create a non-privileged user and transfer ownership
RUN useradd -u 10001 -m appuser && \
    chown -R appuser:appuser /workspace

# Switch to the non-root user
USER appuser

# Expose the designated port
EXPOSE 8000

# Start the application using uvicorn bound to all interfaces
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]