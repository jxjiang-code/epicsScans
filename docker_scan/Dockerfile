# Base image with Miniconda
FROM continuumio/miniconda3:latest

# Set environment variables to avoid buffering
ENV PYTHONUNBUFFERED=1

# Create a Conda environment with Python 3.10
RUN conda create -n pyqt-env python=3.10 pyqt=5.15 -y \
    && echo "conda activate pyqt-env" >> ~/.bashrc

# Activate the conda environment
SHELL ["conda", "run", "-n", "pyqt-env", "/bin/bash", "-c"]

# Install system dependencies required for PyQt5
# Install X11 dependencies for running GUI applications
RUN apt-get update && apt-get install -y --no-install-recommends \
    libx11-dev \
    libxkbfile-dev \
    libglib2.0-0 \
    libsm6 \
    libfontconfig1 \
    libxrender1 \
    libxtst6 \
    tigervnc-standalone-server \
    tigervnc-common \
    tigervnc-tools \ 
    fluxbox \
    qtbase5-dev \
    qttools5-dev-tools \
    qt5-qmake \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*


# Set the working directory inside the container
WORKDIR /app

# Copy the requirements.txt to the container
COPY requirements.txt .

# Install additional dependencies from requirements.txt (if needed)
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Python script into the container
COPY app.py .

# Expose the port (if required for GUI forwarding)
EXPOSE 5901

# Set up VNC password and start VNC server
RUN mkdir -p ~/.vnc && \
    echo "your_vnc_password" | vncpasswd -f > ~/.vnc/passwd && \
    chmod 0600 ~/.vnc/passwd

# Start VNC server and execute the application in the pyqt-env environment
#CMD ["bash", "-c", "vncserver :1 -geometry 1280x1024 -depth 24 && conda init && conda activate pyqt-env && python app.py"]
CMD ["bash", "-c", "vncserver :1 -geometry 1280x1024 -depth 24 "]
