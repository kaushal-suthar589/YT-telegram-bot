FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir \
    yt-dlp \
    ffmpeg-python \
    nest-asyncio \
    python-telegram-bot \
    telegram

# Create downloads directory
RUN mkdir -p downloads

# Run bot
CMD ["python", "main.py"]
