FROM nginx:latest
COPY ./compose/production/nginx/default.conf /etc/nginx/conf.d/default.conf
RUN mkdir -p /usr/share/nginx/ssl
CMD ["nginx", "-g", "daemon off;"]
