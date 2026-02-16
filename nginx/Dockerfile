FROM nginx:1.29-alpine

COPY nginx.conf /etc/nginx/nginx.conf
COPY includes/ /etc/nginx/includes/
COPY ./ssl_certs.sh /ssl_certs.sh
RUN chmod +x /ssl_certs.sh

RUN apk add --no-cache openssl

ENTRYPOINT ["/ssl_certs.sh"]

CMD ["nginx", "-g", "daemon off;"]