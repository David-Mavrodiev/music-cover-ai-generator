# Use an official Python runtime as a parent image
FROM python:3.9

RUN apt-get update && apt-get install -y ffmpeg

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Install any needed packages specified in requirements.txt
# Update pip first to avoid issues
RUN pip install --upgrade pip

# Install Flask, Whisper, OpenAI, and other dependencies
RUN pip install flask openai requests flask-cors git+https://github.com/openai/whisper.git

# Ensure the required directories exist
RUN mkdir -p uploads

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable for Flask
ENV FLASK_APP=api.py

# Run app.py when the container launches
CMD ["flask", "run", "--host=0.0.0.0"]
