# Use the official Python image as a base
FROM python:3.12


# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/

# Install any dependencies
RUN pip install --no-cache-dir -r requirements.txt
    playwright install

# Copy the current directory contents into the container at /app
COPY . /app/

# Expose the port Flask runs on
EXPOSE 5000

# Run the Flask application
CMD ["python", "TwitterTrendingAPI.py"]
