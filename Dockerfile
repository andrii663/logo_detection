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
WORKDIR /logo-server 

# Copy the rest of the application into the container  
COPY . /logo-server  

# Install any needed packages specified in requirements.txt  
RUN pip install --no-cache-dir -r requirements.txt  

# Set folders to be readable, writable, and executable  
RUN sudo chown -R admin:admin /home/admin/storage\
    && sudo chmod -R 0777 /home/admin/storage\
    && sudo chown -R admin:admin /home/admin/config \
    && sudo chmod -R 0777 /home/admin/config  
# Expose the port the app runs on if needed (optional)  
# Make port 5055 available to the world outside this container  
EXPOSE 5055  

# Run the application  
CMD ["python", "app/brokerv4.py"]