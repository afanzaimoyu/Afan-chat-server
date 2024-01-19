FROM nginx:latest
COPY ./compose/production/nginx/default.conf /etc/nginx/conf.d/default.conf
COPY ./compose/production/nginx/MP_verify_GTPosqCvKIDnld6z.txt /usr/share/nginx/html/MP_verify_GTPosqCvKIDnld6z.txt
RUN mkdir -p /usr/share/nginx/ssl
COPY ./compose/production/nginx/ssl /usr/share/nginx/ssl
CMD ["nginx", "-g", "daemon off;"]
