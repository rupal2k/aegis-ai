FROM nginx:1.27-alpine

# Generate self-signed cert for development.
# For production: mount real certs at /etc/nginx/certs/aegis.crt and aegis.key
RUN apk add --no-cache openssl \
 && mkdir -p /etc/nginx/certs \
 && openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
      -keyout /etc/nginx/certs/aegis.key \
      -out    /etc/nginx/certs/aegis.crt \
      -subj "/CN=aegis-ai/O=AegisAI/C=IN"

COPY nginx.conf /etc/nginx/nginx.conf
