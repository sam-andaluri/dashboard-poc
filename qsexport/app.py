from datetime import datetime
from pandas import DataFrame
import boto3

metricDataQuery="""
{
    "Id": "elbResetCount",
    "MetricStat": {
        "Metric": {
            "Namespace": "AWS/NetworkELB",
            "MetricName": "TCP_Target_Reset_Count",
            "Dimensions": [
                {
                    "Name": "LoadBalancer",
                    "Value": "net/iad-broker-61617/1104fb44515b4cdd"
                }
            ]
        },
        "Period": 300,
        "Stat": "Average",
        "Unit": "Count"
    }
}
"""

def lambda_handler(event, context):
    cw = boto3.client(service_name='cloudwatch')
    resp = cw.get_metric_data(MetricDataQueries=metricDataQuery,
                       StartTime=datetime(2020,6,1),
                       EndTime=datetime(2020,6,6),
                       ScanBy='TimestampDescending')
    for mdr in resp['MetricDataResults']:
      label = mdr['Label']
      ts = mdr['Timestamps']
      vals = mdr['Values']
    data = {'Timestamps': ts, 'Values': vals}
    df = DataFrame(data=data)
    df.to_csv("/tmp/cw2qs-%s.csv" % label, index=False)


