# Base image with Python installed
FROM python:3.10-slim

# Set environment variables to avoid buffering
ENV PYTHONUNBUFFERED=1

# Install necessary Linux dependencies for PyQt5
RUN apt-get update && apt-get install -y \
    python3-pyqt5 \
    libgl1-mesa-glx \
    libxcb-xinerama0 \
    && apt-get clean

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY app.py .

# Expose the port (if required for GUI forwarding)
EXPOSE 5000

# Run the Python script
CMD ["python", "app.py"]

