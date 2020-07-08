from datetime import datetime
from datetime import date
from pandas import DataFrame
import boto3
import json

def lambda_handler(event, context):
    dateToday = date.today()
    s3 = boto3.client(service_name='s3')
    cw = boto3.client(service_name='cloudwatch')
    metricDataQuery = """
    [
            {
                "Id": "networkPacketsOut",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/EC2",
                        "MetricName": "NetworkPacketsOut",
                        "Dimensions": [
                            {
                                "Name": "InstanceId",
                                "Value": "i-06f1e283b616c7118"
                            }
                        ]
                    },
                    "Period": 300,
                    "Stat": "Average",
                    "Unit": "Count"
                }
            },
            {
                "Id": "networkPacketsIn",
                "MetricStat": {
                    "Metric": {
                        "Namespace": "AWS/EC2",
                        "MetricName": "NetworkPacketsIn",
                        "Dimensions": [
                            {
                                "Name": "InstanceId",
                                "Value": "i-06f1e283b616c7118"
                            }
                        ]
                    },
                    "Period": 300,
                    "Stat": "Average",
                    "Unit": "Count"
                }
            }
    ]
    """
    resp = cw.get_metric_data(MetricDataQueries=json.loads(metricDataQuery),
        StartTime=datetime(dateToday.year,dateToday.month,dateToday.day-1),
        EndTime=datetime(dateToday.year, dateToday.month, dateToday.day),
        ScanBy='TimestampDescending')
    data = DataFrame()
    for mdr in resp['MetricDataResults']:
        label = mdr['Label']
        ts = mdr['Timestamps']
        vals = mdr['Values']
        if not 'Timestamps' in data.columns:
            data['Timestamps'] = ts
        data[label] = vals
        qsExportFile = "cw2qs-net.csv"
        data.to_csv("/tmp/%s" % qsExportFile, index=False)
        s3.upload_file("/tmp/%s" % qsExportFile, 'aig-cw-qs', qsExportFile)




