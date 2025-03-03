# Use the official Python image as a base
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the Flask app port
EXPOSE 5000

# Set environment variables (use .env at runtime)
ENV PYTHONUNBUFFERED=1

# Command to run the Flask app
CMD ["python", "app.py"]
