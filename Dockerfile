FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY day2.py .

RUN mkdir -p /data/input /data/output

ENTRYPOINT ["python", "day2.py"]

CMD ["--input", "/data/input", "--output", "/data/output/report.csv"]FROM python:3.11-slim

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
