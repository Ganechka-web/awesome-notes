#!/bin/sh

CERT_PATH=/etc/ssl/certs/awesome-notes.crt
CERT_KEY_PATH=/etc/ssl/keys/awesome-notes.key

if [ ! -f "${CERT_PATH}" ]; then
    echo "Generating self-signed ssl certs...."

    mkdir -p /etc/ssl/certs /etc/ssl/keys

    openssl req -x509 \
        -nodes \
        -days 365 \
        -newkey rsa:2048 \
        -keyout ${CERT_KEY_PATH} \
        -out ${CERT_PATH} \
        -subj "/CN=awesome-notes.com" 

    chmod 600 "${CERT_KEY_PATH}"
    chmod 644 "${CERT_PATH}"
fi

echo "🚀 Starting nginx..."
exec "$@"