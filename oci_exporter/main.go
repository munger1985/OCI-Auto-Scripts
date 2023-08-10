// Copyright 2015 The Prometheus Authors
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// A simple example exposing fictional RPC latencies with different types of
// random distributions (uniform, normal, and exponential) as Prometheus
// metrics.
package main

import (
	"context"
	"flag"
	"fmt"
	"github.com/oracle/oci-go-sdk/v65/common"
	"github.com/oracle/oci-go-sdk/v65/monitoring"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"
	"gopkg.in/yaml.v3"
	"log"
	"net/http"
	"os"
	"time"
)

type customPrometheusMetric struct {
	GaugeVecMetric *prometheus.GaugeVec
}
type metricDetail struct {
	Name          string `yaml:"name"`
	Help          string `yaml:"help"`
	Type          string `yaml:"type"`
	Interval      int    `yaml:"interval"`
	Mql           string `yaml:"mql"`
	Namespace     string `yaml:"namespace"`
	CompartmentId string `yaml:"compartmentId"`
	Label1        string `yaml:"label1"`
	Label2        string `yaml:"label2"`
}

type config struct {
	MetricDetails []metricDetail `yaml:"metrics"`
}

/*
Get the value of the metric, aka data point of this certain metric
*/
func GetDp(client monitoring.MonitoringClient, metricDetail metricDetail, m2 *customPrometheusMetric) {
	println(metricDetail.Mql)

	current := time.Now()
	current = current.Add(-1 * time.Minute)
	endTime := current.Add(1 * time.Minute)
	//endTime := current.Add(time.Duration(metricSample.Interval) * time.Minute)
	req := monitoring.SummarizeMetricsDataRequest{CompartmentId: common.String(metricDetail.CompartmentId),
		//CompartmentIdInSubtree: common.Bool(true),
		//	OpcRequestId: common.String("oci_exporter<unique_ID>"),
		SummarizeMetricsDataDetails: monitoring.SummarizeMetricsDataDetails{
			//ResourceGroup: common.String("EXAMPLE-resourceGroup-Value"),
			StartTime: &common.SDKTime{Time: current},
			EndTime:   &common.SDKTime{Time: endTime},
			Namespace: common.String(metricDetail.Namespace),
			Query:     common.String(metricDetail.Mql),
			//Resolution: common.String("EXAMPLE-resolution-Value")
		}}
	resp, err := client.SummarizeMetricsData(context.Background(), req)

	if len(resp.Items) == 0 {
		return
	}

	resourceId := resp.Items[0].Dimensions["resourceId"]
	value := resp.Items[0].AggregatedDatapoints[0].Value
	if err != nil {
		log.Println(err)
	}
	defer func() {
		if err := recover(); err != nil {
			log.Println("恐慌异常:", err)
			return
		}
	}()
	labels := prometheus.Labels{"ocid": resourceId, "label1": metricDetail.Label1, "label2": metricDetail.Label2}

	m2.GaugeVecMetric.With(labels).Set(*value)
	return
}

/*
Get the value of the metric, it will give out a lot of data points for this MQL
*/
func GetManyDps(client monitoring.MonitoringClient, metricDetail *metricDetail, m2 *customPrometheusMetric) {
	println(metricDetail.Type + " " + metricDetail.Mql)
	current := time.Now()
	current = current.Add(-1 * time.Minute)
	endTime := current.Add(1 * time.Minute)
	//endTime := current.Add(time.Duration(metricSample.Interval) * time.Minute)
	req := monitoring.SummarizeMetricsDataRequest{CompartmentId: common.String(metricDetail.CompartmentId),
		//CompartmentIdInSubtree: common.Bool(true),
		//OpcRequestId: common.String("oci_exporter_many<unique_ID>"),
		SummarizeMetricsDataDetails: monitoring.SummarizeMetricsDataDetails{
			//ResourceGroup: common.String("EXAMPLE-resourceGroup-Value"),
			StartTime: &common.SDKTime{Time: current},
			EndTime:   &common.SDKTime{Time: endTime},
			Namespace: common.String(metricDetail.Namespace),
			Query:     common.String(metricDetail.Mql),
			//Resolution: common.String("EXAMPLE-resolution-Value")
		}}
	resp, err := client.SummarizeMetricsData(context.Background(), req)
	for i := 0; i < len(resp.Items); i++ {
		m2.GaugeVecMetric.WithLabelValues(resp.Items[i].Dimensions["resourceId"], metricDetail.Label1, metricDetail.Label2).Set(*(resp.Items[i].AggregatedDatapoints[0].Value))
	}
	if err != nil {
		log.Println(err)
	}
	defer func() {
		if err := recover(); err != nil {
			log.Println("恐慌异常:", err)
			return
		}
	}()

	return
}
func RegisterMetrics(reg prometheus.Registerer, metric metricDetail) *customPrometheusMetric {
	cm := &customPrometheusMetric{

		GaugeVecMetric: prometheus.NewGaugeVec(prometheus.GaugeOpts{
			Name: metric.Name,
			Help: metric.Help,
		}, []string{"ocid", "label1", "label2"}),
	}
	reg.MustRegister(cm.GaugeVecMetric)
	return cm
}

//	func RegisterMetrics(reg prometheus.Registerer, normMean, normDomain float64) *metrics {
//		m := &metrics{
//			// Create a summary to track fictional inter service RPC latencies for three
//			// distinct services with different latency distributions. These services are
//			// differentiated via a "service" label.
//			rpcDurations: prometheus.NewSummaryVec(
//				prometheus.SummaryOpts{
//					Name:       "rpc_durations_seconds",
//					Help:       "RPC latency distributions.",
//					Objectives: map[float64]float64{0.5: 0.05, 0.9: 0.01, 0.99: 0.001},
//				},
//				[]string{"service"},
//			),
//			// The same as above, but now as a histogram, and only for the
//			// normal distribution. The histogram features both conventional
//			// buckets as well as sparse buckets, the latter needed for the
//			// experimental native histograms (ingested by a Prometheus
//			// server v2.40 with the corresponding feature flag
//			// enabled). The conventional buckets are targeted to the
//			// parameters of the normal distribution, with 20 buckets
//			// centered on the mean, each half-sigma wide. The sparse
//			// buckets are always centered on zero, with a growth factor of
//			// one bucket to the next of (at most) 1.1. (The precise factor
//			// is 2^2^-3 = 1.0905077...)
//			rpcDurationsHistogram: prometheus.NewHistogram(prometheus.HistogramOpts{
//				Name:                        "rpc_durations_histogram_seconds",
//				Help:                        "RPC latency distributions.",
//				Buckets:                     prometheus.LinearBuckets(normMean-5*normDomain, .5*normDomain, 20),
//				NativeHistogramBucketFactor: 1.1,
//			}),
//		}
//
//		reg.MustRegister(m.rpcDurations)
//		reg.MustRegister(m.rpcDurationsHistogram)
//		return m
//	}
//
// func SetValueForMetric(m *customMetric, value float64, client monitoring.MonitoringClient) {
//
// }
func main() {
	var (
		addr       = flag.String("listen-address", ":8080", "The address to listen on for HTTP requests.")
		configFile = flag.String("config", "C:\\Users\\opc\\.oci\\config", "The path to the oci api key config file.")
		//uniformDomain     = flag.Float64("uniform.domain", 0.0002, "The domain for the uniform distribution.")
		//normDomain        = flag.Float64("normal.domain", 0.0002, "The domain for the normal distribution.")
		//normMean          = flag.Float64("normal.mean", 0.00001, "The mean for the normal distribution.")
		//oscillationPeriod = flag.Duration("oscillation-period", 10*time.Minute, "The duration of the rate oscillation period.")
	)

	flag.Parse()
	//data, err2 := os.ReadFile("metrics.yaml")
	ss := "metrics.yaml"
	//ss := "C:\\Users\\opc\\Downloads\\prometheus-2.43.0.windows-amd64\\client_golang\\examples\\random\\metrics.yaml"
	data, _ := os.ReadFile(ss)

	fmt.Println(configFile)
	var config config
	yaml.Unmarshal(data, &config)
	//print(config.MetricDetails[1].Labels)
	//for k, v := range config.MetricDetails[1].Labels {
	//	fmt.Println(k, v)
	//}

	configPro, _ := common.ConfigurationProviderFromFile(*configFile, "")

	client, _ := monitoring.NewMonitoringClientWithConfigurationProvider(configPro)

	// Create a non-global registry.
	reg := prometheus.NewRegistry()
	for _, metricDetail := range config.MetricDetails {
		localmetricData := metricDetail
		if localmetricData.Type == "single" {
			m2 := RegisterMetrics(reg, localmetricData)
			go func() {
				for range time.Tick(time.Duration(localmetricData.Interval) * time.Minute) {
					GetDp(client, localmetricData, m2)

				}
			}()
		} else {

			m2 := RegisterMetrics(reg, localmetricData)
			go func() {
				for range time.Tick(time.Duration(localmetricData.Interval) * time.Minute) {
					GetManyDps(client, &localmetricData, m2)
				}
			}()
		}
		//GetDp(client, metricDetail)
		//set value

		// Do something with metric
	}
	// Create new metrics and register them using the custom registry.
	//m := RegisterMetrics(reg, *normMean, *normDomain)
	//for each metric in config.MetricDetails

	// Add Go module build info.
	//reg.MustRegister(collectors.NewBuildInfoCollector())

	//start := time.Now()
	//
	//oscillationFactor := func() float64 {
	//	return 2 + math.Sin(math.Sin(2*math.Pi*float64(time.Since(start))/float64(*oscillationPeriod)))
	//}

	// Periodically record some sample latencies for the three services.
	//go func() {
	//	for {
	//		v := rand.Float64() * *uniformDomain
	//		m.rpcDurations.WithLabelValues("uniform").Observe(v)
	//		time.Sleep(time.Duration(100*oscillationFactor()) * time.Millisecond)
	//	}
	//}()

	// Create a request and dependent object(s).

	// Periodically record some sample latencies for the three services.

	//go func() {
	//	for {
	//		v := (rand.NormFloat64() * *normDomain) + *normMean
	//		m.rpcDurations.WithLabelValues("normal").Observe(v)
	//		// Demonstrate exemplar support with a dummy ID. This
	//		// would be something like a trace ID in a real
	//		// application.  Note the necessary type assertion. We
	//		// already know that rpcDurationsHistogram implements
	//		// the ExemplarObserver interface and thus don't need to
	//		// check the outcome of the type assertion.
	//		m.rpcDurationsHistogram.(prometheus.ExemplarObserver).ObserveWithExemplar(
	//			v, prometheus.Labels{"dummyID": fmt.Sprint(rand.Intn(100000))},
	//		)
	//		time.Sleep(time.Duration(75*oscillationFactor()) * time.Millisecond)
	//	}
	//}()
	//
	//go func() {
	//	for {
	//		v := rand.ExpFloat64() / 1e6
	//		m.rpcDurations.WithLabelValues("exponential").Observe(v)
	//		time.Sleep(time.Duration(50*oscillationFactor()) * time.Millisecond)
	//	}
	//}()

	// Expose the registered metrics via HTTP.
	http.Handle("/metrics", promhttp.HandlerFor(
		reg,
		promhttp.HandlerOpts{
			// Opt into OpenMetrics to support exemplars.
			EnableOpenMetrics: true,
			// Pass custom registry
			Registry: reg,
		},
	))
	log.Fatal(http.ListenAndServe(*addr, nil))
}
