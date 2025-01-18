#include "mbedtls/net_sockets.h"
#include "mbedtls/ssl.h"
#include "mbedtls/entropy.h"
#include "mbedtls/ctr_drbg.h"
#include "mbedtls/error.h"
#include "mbedtls/platform.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define SERVER_PORT "443"
#define RESPONSE_BUFFER_SIZE 2048
#define PARURL "/p/2vEzkK2jOBYARprHnXvN0272zPC0H55RXRg4jwaJVP9FBfSlFT9CUH-jdWmWn1C6/n/sehubjapacprod/b/velero/o/"
#define  HOST "objectstorage.ap-singapore-1.oraclecloud.com"

const int max_retries = 5;
const int retry_interval = 2;  // Initial retry interval (seconds)

void handle_error(const char *msg, int ret) {
    char error_buf[256];
    mbedtls_strerror(ret, error_buf, sizeof(error_buf));
    fprintf(stderr, "%s: -0x%x (%s)\n", msg, -ret, error_buf);
}

int upload_file_with_mbedtls(const char *file_path, const char *host) {
    mbedtls_net_context server_fd;
    mbedtls_ssl_context ssl;
    mbedtls_ssl_config conf;
    mbedtls_entropy_context entropy;
    mbedtls_ctr_drbg_context ctr_drbg;
    char request[4096];
    char response[RESPONSE_BUFFER_SIZE];

    FILE *file = fopen(file_path, "rb");
    if (!file) {
        perror("Failed to open file");
        return -1;
    }

    fseek(file, 0, SEEK_END);
    size_t file_size = ftell(file);
    rewind(file);

    const char *put_url_prefix = PARURL;
    char put_url[2048];
    snprintf(put_url, sizeof(put_url), "%s%s", put_url_prefix, strrchr(file_path, '/') ? strrchr(file_path, '/') + 1 : file_path);

    mbedtls_net_init(&server_fd);
    mbedtls_ssl_init(&ssl);
    mbedtls_ssl_config_init(&conf);
    mbedtls_entropy_init(&entropy);
    mbedtls_ctr_drbg_init(&ctr_drbg);

    if (mbedtls_ctr_drbg_seed(&ctr_drbg, mbedtls_entropy_func, &entropy, NULL, 0) != 0) {
        handle_error("Failed to initialize CTR-DRBG", -1);
        return -1;
    }

    if (mbedtls_ssl_config_defaults(&conf, MBEDTLS_SSL_IS_CLIENT, MBEDTLS_SSL_TRANSPORT_STREAM, MBEDTLS_SSL_PRESET_DEFAULT) != 0) {
        handle_error("Failed to configure SSL", -1);
        return -1;
    }

    mbedtls_ssl_conf_authmode(&conf, MBEDTLS_SSL_VERIFY_OPTIONAL);
    mbedtls_ssl_conf_rng(&conf, mbedtls_ctr_drbg_random, &ctr_drbg);
    mbedtls_ssl_setup(&ssl, &conf);
    mbedtls_ssl_set_hostname(&ssl, host);

    if (mbedtls_net_connect(&server_fd, host, SERVER_PORT, MBEDTLS_NET_PROTO_TCP) != 0) {
        handle_error("Failed to connect to server", -1);
        return -1;
    }

    mbedtls_ssl_set_bio(&ssl, &server_fd, mbedtls_net_send, mbedtls_net_recv, NULL);

    snprintf(request, sizeof(request),
             "PUT %s HTTP/1.1\r\n"
             "Host: %s\r\n"
             "Content-Length: %zu\r\n"
             "Content-Type: application/octet-stream\r\n"
             "\r\n",
             put_url, host, file_size);

    size_t sent = 0;
    while (sent < strlen(request)) {
        int retry_count = 0;
        int ret = mbedtls_ssl_write(&ssl, (const unsigned char *)(request + sent), strlen(request) - sent);
        while (retry_count < max_retries) {
            if (ret > 0) {
                sent += ret;
                break;
            } else if (ret == MBEDTLS_ERR_SSL_WANT_READ || ret == MBEDTLS_ERR_SSL_WANT_WRITE) {
                continue;
            } else {
                handle_error("Failed to send request headers", ret);
                retry_count++;
                printf("Retrying in %d seconds...\n", retry_interval * retry_count);
                sleep(retry_interval * retry_count);
                return -1;
            }
        }
    }

    char buffer[1024];
    size_t bytes_read;
    while ((bytes_read = fread(buffer, 1, sizeof(buffer), file)) > 0) {
        sent = 0;
        while (sent < bytes_read) {
            int ret = mbedtls_ssl_write(&ssl, (const unsigned char *)(buffer + sent), bytes_read - sent);
            int retry_count = 0;

            while (retry_count < max_retries) {

                    if (ret > 0) {
                        sent += ret;
                        break;
                    } else if (ret == MBEDTLS_ERR_SSL_WANT_READ || ret == MBEDTLS_ERR_SSL_WANT_WRITE) {
                        continue;
                    } else {
                        handle_error("Failed to send file content", ret);
                        retry_count++;
                        printf("Retrying in %d seconds...\n", retry_interval * retry_count);
                        sleep(retry_interval * retry_count);
                        fclose(file);
                        return -1;
                    }
                }
            }
    }

    fclose(file);

    int ret = mbedtls_ssl_read(&ssl, (unsigned char *)response, sizeof(response) - 1);
    if (ret > 0) {
        response[ret] = '\0';
        printf("Server response: %s\n", response);
    } else {
        handle_error("Failed to read server response", ret);
    }

    mbedtls_ssl_free(&ssl);
    mbedtls_net_free(&server_fd);
    mbedtls_ssl_config_free(&conf);
    mbedtls_ctr_drbg_free(&ctr_drbg);
    mbedtls_entropy_free(&entropy);

    return 0;
}

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <file_path>\n", argv[0]);
        return 1;
    }

    const char *file_path = argv[1];
    const char *host = HOST;

    if (upload_file_with_mbedtls(file_path, host) == 0) {
        printf("File uploaded successfully.\n");
    } else {
        printf("File upload failed.\n");
    }
    return 0;
}
