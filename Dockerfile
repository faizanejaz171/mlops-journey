FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your script
COPY day1.py .

# Your images folder (we'll mount it, not copy)
VOLUME ["/app/images"]

# Run the script
CMD ["python", "day1.py"]
