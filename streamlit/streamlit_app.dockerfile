FROM python:3.11-slim

RUN pip install  --no-cache-dir poetry==1.6.1

RUN poetry config virtualenvs.create false

WORKDIR /code

# Copy dependency files
COPY ./pyproject.toml ./README.md ./poetry.lock* ./

# Copy application code
COPY ./app ./app
COPY ./streamlit ./streamlit

# Install dependencies
RUN poetry install --no-interaction --no-ansi --no-dev --with streamlit            

# Install streamlit
RUN pip install streamlit

# Expose ports for both services
EXPOSE 8080 8501

# Start both services
CMD uvicorn app.server:app --host 0.0.0.0 --port 8080 & streamlit run streamlit/streamlit_app.py --server.port 8501 --server.address 0.0.0.0