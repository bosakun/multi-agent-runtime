FROM python:3.12-slim
WORKDIR /runtime
COPY pyproject.toml README.md ./
COPY app ./app
COPY demos ./demos
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY migrations ./migrations
COPY examples ./examples
RUN useradd --create-home runtime && chown -R runtime:runtime /runtime
USER runtime
EXPOSE 8000
CMD ["uvicorn", "app.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
