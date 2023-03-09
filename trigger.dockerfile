FROM maniator/gh

WORKDIR /usr/src/app

COPY . .

CMD [ "workflow", "run", "spider.yml"]
