FROM python:3.9-slim

# Python-specific environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Setup virtual environment and poetry
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
RUN python3 -m pip install --no-cache-dir -U poetry pip

# Copy bot files
WORKDIR /opt/bot
COPY bot_rio ./bot_rio
COPY pyproject.toml .
RUN python3 -m pip install --no-cache-dir .

# Run bot
COPY main.py .
CMD [ "python", "main.py" ]