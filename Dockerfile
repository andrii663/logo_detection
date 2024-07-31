# Use an official Python runtime as a parent image  
FROM python:3.9-slim  

# Upgrade pip inside the container  
RUN python -m pip install --upgrade pip  

# Install system dependencies that are required for h5py and OpenCV  
RUN apt-get update && apt-get install -y \
    pkg-config \
    libhdf5-dev \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    g++ \
    build-essential \
    && rm -rf /var/lib/apt/lists/*   

# Set environment variables for compilers  
ENV CC=gcc  
ENV CXX=g++  

# Set the working directory in the container  
WORKDIR /license-server 

# Copy the rest of the application into the container  
COPY . /license-server  

# Install any needed packages specified in requirements.txt  
RUN pip install --no-cache-dir -r requirements.txt  

# Expose the port the app runs on if needed (optional)  
# Make port 5031 available to the world outside this container  
EXPOSE 5032  

# Run the application  
CMD ["python", "app/brokerv4.py"]