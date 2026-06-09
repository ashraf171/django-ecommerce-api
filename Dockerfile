FROM python:3.12

COPY requirements.txt . 

RUN pip install -r requirements.txt


COPY . . 

CMD sh -c "python manage.py migrate && gunicorn E_commerce.wsgi:application --bind 0.0.0.0:8000"