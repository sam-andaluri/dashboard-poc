from datetime import datetime
from datetime import date
from pandas import DataFrame
import boto3
import json
import os

s3 = boto3.client(service_name='s3')
orgs = boto3.client('organizations')
accountId = os.environ['ACCOUNT_ID']
accountResp = orgs.describe_account(AccountId=accountId)
accountName = accountResp['Account']['Name']
def phdExport():
    phd = boto3.client(service_name='health')
    response = phd.describe_events()
    data = DataFrame()
    for event in response['events']:
        endTime=""
        if 'endTime' in event:
            endTime = event['endTime']
        else:
            endTime = "None"
        data = data.append({
                     'accountId':accountId,
                     'accountName':accountName,
                     'arn':event['arn'],
                     'service':event['service'],
                     'eventTypeCode':event['eventTypeCode'],
                     'eventTypeCategory':event['eventTypeCategory'],
                     'region':event['region'],
                     'startTime':event['startTime'],
                     'endTime':endTime,
                     'lastUpdatedTime':event['lastUpdatedTime'],
                     'statusCode':event['statusCode']
                     }, ignore_index=True)
    phdFile = "%s-phd.csv" % accountId
    data.to_csv("/tmp/%s" % phdFile, index=False)
    s3.upload_file("/tmp/%s" % phdFile, 'aig-cw-qs', phdFile)

def metricsExport():
    dateToday = date.today()
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


def lambda_handler(event, context):
    metricsExport()
    phdExport()

