import boto3
import json
import os

phdMd = """\n\n#Dashboard - Health Events\n\nService | EventType | EventCategory | Region | StartTime | EndTime | LastUpdated | Status  \n------|------|------|------|------|------|------|------\n"""
phdRowMd = """%s | %s | %s | %s | %s | %s | %s | %s | %s\n"""

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

def lambda_handler(event, context):
    global phdMd
    phd = boto3.client(service_name='health')
    cw = boto3.client(service_name='cloudwatch')
    response = phd.describe_events()
    for event in response['events']:
        print(event)
        eventArn = event['arn']
        eventDetailsResp = phd.describe_event_details(eventArns=[eventArn])
        # TODO - Add event details dashboard
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
        details = eventDetailsResp['successfulSet'][0]['eventDescription']['latestDescription']
        phdMd += phdRowMd % (
        service, eventType, eventCategory, region, startTime, endTime, lastUpdTime, status, details)
    phdJson = json.loads(phdDashboard, strict=False)
    phdJson['widgets'][0]['properties']['markdown'] = phdMd
    cw.put_dashboard(DashboardName=os.environ['ACCOUNT_ID'] + '-phd', DashboardBody=json.dumps(phdJson))
