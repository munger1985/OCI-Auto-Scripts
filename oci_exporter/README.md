# I call it Pmore
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
