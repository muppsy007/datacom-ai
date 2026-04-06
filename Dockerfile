FROM python:3.13-slim

WORKDIR /app

# Install PyTorch CPU-only from the lightweight CPU index (no CUDA, ~200MB vs ~2GB)
RUN pip install --no-cache-dir --timeout 300 torch --index-url https://download.pytorch.org/whl/cpu

# Install project dependencies plus streamlit
COPY pyproject.toml .
RUN pip install --no-cache-dir . streamlit

# Copy application code
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.headless", "true", "--server.address", "0.0.0.0"]
