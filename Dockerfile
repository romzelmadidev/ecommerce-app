FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV APP_PORT=5000

# Create working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create a non-root user and change ownership of the application directory
RUN addgroup --system bankgroup && adduser --system --ingroup bankgroup bankuser
RUN chown -R bankuser:bankgroup /app

# Switch to the non-root user
USER bankuser

# Expose port
EXPOSE 5000

# Command to run the application using gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]