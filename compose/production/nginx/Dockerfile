FROM nginx:latest
COPY ./compose/production/nginx/nginx.conf /etc/nginx/nginx.conf
COPY ./compose/production/nginx/MP_verify_GTPosqCvKIDnld6z.txt /usr/share/nginx/html/MP_verify_GTPosqCvKIDnld6z.txt
RUN mkdir -p /usr/share/nginx/ssl
COPY ./compose/production/nginx/ssl /usr/share/nginx/ssl
COPY ./compose/production/nginx/dist /usr/share/nginx/html/www/wwwroot/www.afanchat.cn
CMD ["nginx", "-g", "daemon off;"]
