import boto3
import pprint
import json

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

rootDashboardMd = """\n#Dashboard\n\n"""
rootDashboardDynamicRegion = """\n\n## Region %s\n\n"""
rootDashboardDynamicTableHead = """\n### EC2\nInstance State | Count\n----|-----"""
rootDashboardDynamicTableRow = """\nRunning | %s\nStopped | %s\n"""

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

instancesInStateMd = """\n\n#Dashboard - EC2\n\n## %s Instances\n\nInstanceId | InstanceType | IP Address\n------|------|------\n"""
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
            print(regionName)
            instances = ec2.describe_instances()
            pp = pprint.PrettyPrinter(indent=1)
            pp.pprint(instances)
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
                    print(json.dumps(instMetricsDashboard))
                    cw.put_dashboard(DashboardName="ec2-%s-%s" % (regionName, instanceId), DashboardBody=json.dumps(instMetricsDashboard))
                    instMd = eachInstanceMarkdown % (instURL, instanceType, ipAddress)
                    print(state)
                    print(instMd)
                    if state in markdownDict.keys():
                        markdownDict[state] += instMd
                    else:
                        markdownDict[state] = instMd
                    #print(pp.pprint(instance))
                    if state in stateCount.keys():
                        stateCount[state] += 1
                    else:
                        stateCount[state] = 1
            if (len(stateCount) > 0):
                rootDashboardMd += rootDashboardDynamicRegion % regionName
                rootDashboardMd += rootDashboardDynamicTableHead
                urlRunning = generateNumInstURLMd("ec2", regionName, "running", stateCount['running'])
                urlStopped = generateNumInstURLMd("ec2", regionName, "stopped", stateCount['stopped'])
                rootDashboardMd += rootDashboardDynamicTableRow % (urlRunning, urlStopped)
            if (len(markdownDict) > 0):
                runningInstancesJson = instancesInStateMd % "running".capitalize()
                runningInstancesJson += markdownDict['running']
                stoppedInstancesJson = instancesInStateMd % "stopped".capitalize()
                stoppedInstancesJson += markdownDict['stopped']
                #print(runningInstancesJson)
                #print(stoppedInstancesJson)
                instanceDashboardJson = json.loads(instancesInState, strict=False)
                instanceDashboardJson['widgets'][0]['properties']['markdown'] = runningInstancesJson
                cw.put_dashboard(DashboardName="ec2-%s-running" % regionName, DashboardBody=json.dumps(instanceDashboardJson))
                print(json.dumps(instanceDashboardJson))
                instanceDashboardJson['widgets'][0]['properties']['markdown'] = stoppedInstancesJson
                cw.put_dashboard(DashboardName="ec2-%s-stopped" % regionName, DashboardBody=json.dumps(instanceDashboardJson))
                print(json.dumps(instanceDashboardJson))
    rootDashboardJson = json.loads(rootDashboard, strict=False)
    rootDashboardJson['widgets'][0]['properties']['markdown'] = rootDashboardMd
    print(json.dumps(rootDashboardJson))
    cw.put_dashboard(DashboardName="main-dashboard", DashboardBody=json.dumps(rootDashboardJson))


