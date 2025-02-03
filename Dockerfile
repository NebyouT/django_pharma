# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install PyInstaller
RUN pip install pyinstaller

# Install binutils for PyInstaller
RUN apt-get update && apt-get install -y binutils

# Run PyInstaller to create the executable
RUN pyinstaller --onefile manage.py

# The command to run the executable
CMD ["/app/dist/manage"]
