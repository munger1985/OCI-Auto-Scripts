# I call it oci_exporter
## .exe for windows
## non .exe for linux, mac etc



# usage

 ./oci_exporter when run, it will show usage

 ```
 Usage of ./oci_exporter:
  -config string
        This is required! The path to the oci api key config file. windows: like -config C:\Users\opc\.oci\config; linux like: -config /home/opc/.oci/config
  -listen-address string
        The address to listen on for HTTP requests. (default ":8080")

 ```

# simply config all metrics type to many

## linux

### default is 8080, prometheus will scrape from that, = and space are the same

 ./oci_exporter -config=/home/opc/.oci/config -listen-address=:8081

## windows
 oci_exporter.exe  -config C:\Users\opc\.oci\config


## docker

### Dockerfile

```
FROM golang

# Set environment variables

# Update the package repository and install packages
RUN apt-get update && \
    apt-get install -y \
    iproute2 \
    wget \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set a working directory
WORKDIR /app

# Copy files into the container (if needed)
COPY . /app

RUN chmod +x /app/oci_exporter
```

### build

docker build -t oci_exporter .

### run

docker run  oci_exporter  /app/oci_exporter -config=/app/config

/app/config is api key config file

need to make sure key.pem in config file is existed.
