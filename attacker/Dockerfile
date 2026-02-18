FROM python:3.11-slim

WORKDIR /attack

COPY attack.py .
COPY legit_user.py .

RUN pip install requests beautifulsoup4

CMD ["tail", "-f", "/dev/null"]
