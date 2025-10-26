FROM nginx:stable-alpine
RUN addgroup -S app && adduser -S -G app app
COPY nginx.conf /etc/nginx/nginx.conf
# expect certs mounted at /etc/nginx/certs (bind mount from local)
USER app
