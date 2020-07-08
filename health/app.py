import boto3
import json
import os

phdMd = """\n\n# Dashboard - Health Events\n\nService | EventType | EventCategory | Region | StartTime | EndTime | LastUpdated | Status  \n------|------|------|------|------|------|------|------\n"""
phdRowMd = """%s | %s | %s | %s | %s | %s | %s | %s \n"""
accountId = os.environ['ACCOUNT_ID']
phdDashboard="""
{
    "widgets": [
        {
            "type": "text",
            "x": 0,
            "y": 0,
            "width": 24,
            "height": 12,
            "properties": {
                "markdown": ""
            }
        }
    ]
}
"""

def generateDetailsURLMd(status, region, dashboardCount, accountId):
    return """[%s](https://console.aws.amazon.com/cloudwatch/home?region=%s#dashboards:name=phd-event-details-%d-%s)""" % (
        status, region, dashboardCount, accountId)

def lambda_handler(event, context):
    global phdMd
    phd = boto3.client(service_name='health')
    cw = boto3.client(service_name='cloudwatch')
    response = phd.describe_events()
    detailsDashboardCount = 1
    detailsDashboards = cw.list_dashboards(DashboardNamePrefix='phd-event-details-')
    prevDashboardList = []
    for dashboard in detailsDashboards['DashboardEntries']:
        prevDashboardList.append(dashboard['DashboardName'])
    if len(prevDashboardList) > 0:
        cw.delete_dashboards(DashboardNames=prevDashboardList)
    for event in response['events']:
        eventArn = event['arn']
        eventDetailsResp = phd.describe_event_details(eventArns=[eventArn])
        details = eventDetailsResp['successfulSet'][0]['eventDescription']['latestDescription']
        detailsDashboardName = "phd-event-details-%d-%s" % (detailsDashboardCount,  accountId)
        detailsJson = json.loads(phdDashboard, strict=False)
        detailsJson['widgets'][0]['properties']['markdown'] = details
        cw.put_dashboard(DashboardName=detailsDashboardName, DashboardBody=json.dumps(detailsJson))
        service = event['service']
        eventType = event['eventTypeCode']
        eventCategory = event['eventTypeCategory']
        region = event['region']
        startTime = event['startTime']
        if 'endTime' in event:
            endTime = event['endTime']
        else:
            endTime = "None"
        lastUpdTime = event['lastUpdatedTime']
        status = event['statusCode']
        phdMd += phdRowMd % (
        service, eventType, eventCategory, region, startTime, endTime, lastUpdTime, generateDetailsURLMd(status, region, detailsDashboardCount, accountId))
        detailsDashboardCount += 1
    phdJson = json.loads(phdDashboard, strict=False)
    phdJson['widgets'][0]['properties']['markdown'] = phdMd
    cw.put_dashboard(DashboardName=accountId + '-phd', DashboardBody=json.dumps(phdJson))
