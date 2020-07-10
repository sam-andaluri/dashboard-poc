import boto3
import json
from pytz import timezone
from datetime import datetime
import os

rootDashboard="""
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

accountId = os.environ['ACCOUNT_ID']
dateInUTC = datetime.now(timezone('UTC'))
dashboardDate = dateInUTC.strftime("%m/%d/%Y %H:%M:%S %Z")
rootDashboardMd = """\n# Dashboard\n\n### Last Updated: """ + dashboardDate + """\n\n """
rootDashboardDynamicRegion = """\n\n## Region %s\n\n"""
rootDashboardDynamicTableHead = """\n### EC2\nInstance State | Count\n----|-----"""
rootDashboardDynamicTableRow = """\nRunning | %s\nStopped | %s\n"""
rootDashboardFootNote = """\n\n## Other Links\n\n Dashboard Type | Link\n----|-----\nQuotas | [Quotas](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=%s-quotas)\nPhd | [Phd](https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=%s-phd)\n"""

instancesInState="""
{
    "widgets": [
        {
            "type": "text",
            "x": 0,
            "y": 0,
            "width": 24,
            "height": 9,
            "properties": {
                "markdown": ""
            }
        }
    ]
}
"""

instanceDashboard="""
{
    "widgets": [
        {
            "type": "metric",
            "x": 0,
            "y": 6,
            "width": 24,
            "height": 6,
            "properties": {
                "metrics": [
                    [ "AWS/EC2", "NetworkIn", "InstanceId", "%s" ],
                    [ ".", "NetworkOut", ".", "." ]
                ],
                "view": "timeSeries",
                "stacked": false,
                "region": "%s",
                "period": 300,
                "stat": "Average"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 12,
            "width": 24,
            "height": 6,
            "properties": {
                "view": "timeSeries",
                "stacked": false,
                "metrics": [
                    [ "AWS/EC2", "EBSReadOps", "InstanceId", "%s" ],
                    [ ".", "EBSWriteOps", ".", "." ]
                ],
                "region": "%s"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 18,
            "width": 24,
            "height": 6,
            "properties": {
                "view": "timeSeries",
                "stacked": false,
                "metrics": [
                    [ "AWS/EC2", "NetworkPacketsIn", "InstanceId", "%s" ],
                    [ ".", "NetworkPacketsOut", ".", "." ]
                ],
                "region": "%s"
            }
        },
        {
            "type": "metric",
            "x": 0,
            "y": 0,
            "width": 24,
            "height": 6,
            "properties": {
                "view": "timeSeries",
                "stacked": false,
                "metrics": [
                    [ "AWS/EC2", "EBSByteBalance%", "InstanceId", "%s" ],
                    [ ".", "CPUUtilization", ".", "." ]
                ],
                "region": "%s"
            }
        }
    ]
}
"""

instancesInStateMd = """\n\n# Dashboard - EC2\n\n## %s Instances\n\nInstanceId | InstanceType | IP Address\n------|------|------\n"""
eachInstanceMarkdown = """%s | %s | %s\n"""

def generateInstURLMd(instanceId, region):
    return """[%s](https://console.aws.amazon.com/cloudwatch/home?region=%s#dashboards:name=ec2-%s-%s)""" % (instanceId, region, region, instanceId)

def generateNumInstURLMd(service, region, state, numInstances):
    return """[%d](https://console.aws.amazon.com/cloudwatch/home?region=%s#dashboards:name=%s-%s-%s)""" % (numInstances, region, service, region, state)

def lambda_handler(event, context):
    global rootDashboardMd
    ec2 = boto3.client('ec2')
    regions = ec2.describe_regions()
    for region in regions['Regions']:
        optIn = region['OptInStatus']
        regionName = region['RegionName']
        cw = boto3.client(service_name='cloudwatch', region_name=regionName)
        if optIn != 'not-opted-in':
            ec2 = boto3.client(service_name='ec2', region_name=regionName)
            instances = ec2.describe_instances()
            stateCount = {}
            markdownDict = {}
            for reservation in instances['Reservations']:
                for instance in reservation['Instances']:
                    state = instance['State']['Name']
                    instanceId = instance['InstanceId']
                    instanceType = instance['InstanceType']
                    ipAddress = instance['PrivateIpAddress']
                    instURL = generateInstURLMd(instanceId, regionName)
                    instMetricsDashboard = json.loads(instanceDashboard, strict=False)
                    for widget in instMetricsDashboard['widgets']:
                        widget['properties']['metrics'][0][3] = instanceId
                        widget['properties']['region'] = regionName
                    cw.put_dashboard(DashboardName="ec2-%s-%s" % (regionName, instanceId), DashboardBody=json.dumps(instMetricsDashboard))
                    instMd = eachInstanceMarkdown % (instURL, instanceType, ipAddress)
                    if state in markdownDict.keys():
                        markdownDict[state] += instMd
                    else:
                        markdownDict[state] = instMd
                    if state in stateCount.keys():
                        stateCount[state] += 1
                    else:
                        stateCount[state] = 1
            if (len(stateCount) > 0):
                rootDashboardMd += rootDashboardDynamicRegion % regionName
                rootDashboardMd += rootDashboardDynamicTableHead
                if 'running' in stateCount.keys():
                    urlRunning = generateNumInstURLMd("ec2", regionName, "running", stateCount['running'])
                else:
                    urlRunning = "0"
                if 'stopped' in stateCount.keys():
                    urlStopped = generateNumInstURLMd("ec2", regionName, "stopped", stateCount['stopped'])
                else:
                    urlStopped = "0"
                rootDashboardMd += rootDashboardDynamicTableRow % (urlRunning, urlStopped)
            if (len(markdownDict) > 0):
                instanceDashboardJson = json.loads(instancesInState, strict=False)
                if 'running' in markdownDict.keys():
                    runningInstancesJson = instancesInStateMd % "running".capitalize()
                    runningInstancesJson += markdownDict['running']
                    instanceDashboardJson['widgets'][0]['properties']['markdown'] = runningInstancesJson
                    cw.put_dashboard(DashboardName="ec2-%s-running" % regionName, DashboardBody=json.dumps(instanceDashboardJson))
                if 'stopped' in markdownDict.keys():
                    stoppedInstancesJson = instancesInStateMd % "stopped".capitalize()
                    stoppedInstancesJson += markdownDict['stopped']
                    instanceDashboardJson['widgets'][0]['properties']['markdown'] = stoppedInstancesJson
                    cw.put_dashboard(DashboardName="ec2-%s-stopped" % regionName, DashboardBody=json.dumps(instanceDashboardJson))
    rootDashboardMd += (rootDashboardFootNote % (accountId, accountId))
    rootDashboardJson = json.loads(rootDashboard, strict=False)
    rootDashboardJson['widgets'][0]['properties']['markdown'] = rootDashboardMd
    cw.put_dashboard(DashboardName="main-dashboard", DashboardBody=json.dumps(rootDashboardJson))


