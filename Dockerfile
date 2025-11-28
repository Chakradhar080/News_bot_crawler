# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Install cron
RUN apt-get update && apt-get install -y cron

# Set the working directory
WORKDIR /home/news_bot

# Copy everything from the news_bot directory on the host to /home/news_bot in the container
COPY . /home/news_bot

# Install any necessary dependencies
RUN pip install --no-cache-dir -r /home/news_bot/requirements.txt

# Add the cron job
COPY cron-job /etc/cron.d/your-cron-job

# Give execution rights on the cron job
RUN chmod 0644 /etc/cron.d/your-cron-job

# Apply the cron job
RUN crontab /etc/cron.d/your-cron-job

# Create the log file to be able to run tail
RUN touch /var/log/cron.log

# Run the cron service and the script
CMD ["sh", "-c", "cron && tail -f /var/log/cron.log"]

