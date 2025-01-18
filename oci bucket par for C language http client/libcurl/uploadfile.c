#include <stdio.h>
#include <curl/curl.h>
#include <sys/stat.h>
#include <errno.h>
#include <string.h>

// 获取文件大小的函数
static long get_file_size(const char *filename) {
    struct stat file_info;
    if (stat(filename, &file_info) == 0) {
        return file_info.st_size;
    }
    return -1;
}

int main(void) {
    CURL *curl;
    CURLcode res;
    FILE *file;
    const char *filename = "w.txt";
    const char *url = "https://objectstorage.ap-singapore-1.oraclecloud.com/p/ZVs0rZR5IsWKYbRqfhxxIfRjv5c1uKyli9Vp52QyRAUTvvdnFGuBz-jHZB_2pQBs/n/sehubjapacprod/b/velero/o/w.txt";
    
    // 打开文件
    file = fopen(filename, "rb");
    if (!file) {
        fprintf(stderr, "无法打开文件 %s: %s\n", filename, strerror(errno));
        return 1;
    }

    // 获取文件大小
    long file_size = get_file_size(filename);
    if (file_size == -1) {
        fprintf(stderr, "无法获取文件大小\n");
        fclose(file);
        return 1;
    }

    // 初始化 curl
    curl = curl_easy_init();
    if (curl) {
        // 设置上传文件
        curl_easy_setopt(curl, CURLOPT_UPLOAD, 1L);
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_READDATA, file);
        curl_easy_setopt(curl, CURLOPT_INFILESIZE, file_size);
        
        // 如果需要显示详细信息，取消下面这行的注释
        // curl_easy_setopt(curl, CURLOPT_VERBOSE, 1L);

        // 设置SSL验证选项
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 1L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 2L);

        // 执行请求
        res = curl_easy_perform(curl);

        // 检查是否有错误发生
        if (res != CURLE_OK) {
            fprintf(stderr, "上传失败: %s\n", curl_easy_strerror(res));
        } else {
            printf("文件上传成功\n");
            
            // 获取HTTP响应码
            long http_code = 0;
            curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);
            printf("HTTP响应码: %ld\n", http_code);
        }

        // 清理
        curl_easy_cleanup(curl);
    } else {
        fprintf(stderr, "Curl 初始化失败\n");
    }

    // 关闭文件
    fclose(file);

    return (res == CURLE_OK) ? 0 : 1;
}
