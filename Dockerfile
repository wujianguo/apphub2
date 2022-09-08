FROM python:3
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir uwsgi & pip install --no-cache-dir --default-timeout=100 -r requirements.txt
CMD [ "uwsgi", "--ini", "apphub.uwsgi.ini" ]
# docker run -p 8000:8000 -w /app -v "$(pwd):/app" --name apphub --rm -it apphub:latest sh -c "python manage.py runserver 0.0.0.0:8000"
