FROM mysql:latest

COPY ./schema.sql /docker-entrypoint-initdb.d/init.sql
EXPOSE 3306

CMD ["mysqld"]
