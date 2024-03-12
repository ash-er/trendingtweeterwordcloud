# Use the official Python image as a base
FROM python:3.10

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt /app/
COPY TwitterTrendingAPI.py /app/
COPY Default_Twitter_Trending /app/Default_Twitter_Trending

# Install any dependencies
RUN apt-get update && \
    pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install
    playwright install-deps

# Copy the current directory contents into the container at /app
# COPY . /app/

# Expose the port Flask runs on
EXPOSE 5000

# Run the Flask application
CMD ["python3", "TwitterTrendingAPI.py"]
