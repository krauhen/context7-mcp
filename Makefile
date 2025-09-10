IMAGE_NAME=context7
CERTS_DIR=data/certs
TLS_CERT=$(CERTS_DIR)/cert.pem
TLS_KEY=$(CERTS_DIR)/key.pem

.PHONY: all build tls-certs run run-demon

all: tls-certs build run

build:
	docker compose build

tls-certs:
	mkdir -p $(CERTS_DIR)
	openssl req -x509 -newkey rsa:4096 -nodes -days 365 \
        -keyout $(TLS_KEY) -out $(TLS_CERT) \
        -subj "/CN=localhost"

run: build
	docker compose up

run-demon: build
	docker compose up -d