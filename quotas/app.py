import boto3
import json
import os

quotasMd = """\n\n#Demo Dashboard - Quotas\n\nServiceCode | ServiceName | QuotaName | Value | Adjustable | Global\n------|------|------|------|------|------\n"""
quotaRowMd = """%s | %s | %s | %s | %s | %s\n"""
quotasDashboard = """
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

def makeQuotaRows(serviceCode):
    global quotasMd
    sq = boto3.client('service-quotas')
    for svc in serviceCode:
        quotas = sq.list_service_quotas(ServiceCode=svc)
        for quota in quotas['Quotas']:
            quotasMd += quotaRowMd % (
                quota['ServiceCode'], quota['ServiceName'], quota['QuotaName'], str(quota['Value']),
                str(quota['Adjustable']), str(quota['GlobalQuota']))

def lambda_handler(event, context):
    cw = boto3.client(service_name='cloudwatch')
    makeQuotaRows(['ec2', 'ebs', 'elasticloadbalancing'])
    quotasJson = json.loads(quotasDashboard, strict=False)
    quotasJson['widgets'][0]['properties']['markdown'] = quotasMd
    cw.put_dashboard(DashboardName=os.environ['ACCOUNT_ID'] + '-quotas', DashboardBody=json.dumps(quotasJson))

