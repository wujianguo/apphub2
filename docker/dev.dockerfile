FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install --no-cache-dir uwsgi & pip install --no-cache-dir -r requirements.txt
# docker build -f dev.dockerfile . -t apphub-python # --network=host
# docker run -p 8000:8000 -w /app -v "$(pwd):/app" --name apphub-api --rm -it apphub-python:latest sh -c "python manage.py collectstatic"
# docker run -p 8000:8000 -w /app -v "$(pwd):/app" --name apphub-api --rm -it apphub-python:latest sh -c "python manage.py migrate"
# docker run -p 8000:8000 -w /app -v "$(pwd):/app" --name apphub-api --rm -it apphub-python:latest sh -c "python manage.py runserver 0.0.0.0:8000"
