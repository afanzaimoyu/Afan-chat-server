FROM python:3.12.0

LABEL maintainer="flz"

#RUN apt-get update && apt-get install --no-install-recommends -y \
#  sudo git bash-completion nano ssh
# Python 'run' stage
RUN echo "Types: deb" > /etc/apt/sources.list.d/debian.sources \
    && echo "URIs: https://mirrors.tuna.tsinghua.edu.cn/debian" >> /etc/apt/sources.list.d/debian.sources \
    && echo "Suites: bookworm bookworm-updates" >> /etc/apt/sources.list.d/debian.sources \
    && echo "Components: main" >> /etc/apt/sources.list.d/debian.sources
RUN apt update && apt -y install ncat

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app
COPY . ${APP_HOME}


ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV BUILD_ENV ${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -U pip \
    && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

#COPY  ./compose/production/django/entrypoint /entrypoint
#RUN sed -i 's/\r$//g' /entrypoint
#RUN chmod +x /entrypoint


COPY  ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

COPY  ./compose/production/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r$//g' /start-celeryworker
RUN chmod +x /start-celeryworker


#COPY  ./compose/production/django/celery/beat/start /start-celerybeat
#RUN sed -i 's/\r$//g' /start-celerybeat
#RUN chmod +x /start-celerybeat
#
#
#COPY ./compose/production/django/celery/flower/start /start-flower
#RUN sed -i 's/\r$//g' /start-flower
#RUN chmod +x /start-flower

#ENTRYPOINT ["/entrypoint"]
