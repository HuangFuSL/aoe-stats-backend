FROM python:3.10.10-bullseye

WORKDIR /usr/src/app

ENV fc=1

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "-m", "src" ]