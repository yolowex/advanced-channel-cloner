# Use the official Python image from the Docker Hub
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy the pyproject.toml and poetry.lock files into the container
COPY pyproject.toml poetry.lock ./

# Install the dependencies
RUN poetry install

# Copy the rest of the application code into the container
COPY . .

# Command to run the bot
CMD ["poetry", "run", "python", "main.py"]

