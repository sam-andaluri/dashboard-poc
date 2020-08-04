import boto3
import os

topicArn = os.environ['SNS_TOPIC_ARN']
def putALBAlarm(region, instanceId, unit, metric, threshold, topicArn):
    cw = boto3.client(service_name='cloudwatch' , region_name=region)
    cw.put_metric_alarm(
        AlarmName="ALB-" + instanceId,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName=metric,
        Namespace="AWS/ApplicationELB",
        Period=60,
        Statistic='Average',
        Threshold=threshold,
        ActionsEnabled=True,
        OKActions=[
            topicArn,
        ],
        AlarmActions=[
            topicArn,
        ],
        AlarmDescription= metric + ' exceeded ' + threshold + ' for ' + instanceId,
        Dimensions=[
            {
                'Name' : "LoadBalancer",
                'Value' : instanceId
            },
        ],
        Unit=unit
    )

def putEBSAlarm(region, instanceId, unit, metric, threshold, topicArn):
    cw = boto3.client(service_name='cloudwatch' , region_name=region)
    cw.put_metric_alarm(
        AlarmName="EBS-" + instanceId,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName=metric,
        Namespace="AWS/EBS",
        Period=60,
        Statistic='Average',
        Threshold=threshold,
        ActionsEnabled=True,
        OKActions=[
            topicArn,
        ],
        AlarmActions=[
            topicArn,
        ],
        AlarmDescription= metric + ' exceeded ' + threshold + ' for ' + instanceId,
        Dimensions=[
            {
                'Name' : "VolumeId",
                'Value' : instanceId
            },
        ],
        Unit=unit
    )

def putRDSAlarm(region, instanceId, unit, metric, threshold, topicArn):
    cw = boto3.client(service_name='cloudwatch' , region_name=region)
    cw.put_metric_alarm(
        AlarmName="RDS-" + instanceId,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName=metric,
        Namespace="AWS/RDS",
        Period=60,
        Statistic='Average',
        Threshold=threshold,
        ActionsEnabled=True,
        OKActions=[
            topicArn,
        ],
        AlarmActions=[
            topicArn,
        ],
        AlarmDescription= metric + ' exceeded ' + threshold + ' for ' + instanceId,
        Dimensions=[
            {
                'Name' : "DBInstanceIdentifier",
                'Value' : instanceId
            },
        ],
        Unit=unit
    )

def putEC2Alarm(region, instanceId, unit, metric, threshold, topicArn):
    cw = boto3.client(service_name='cloudwatch' , region_name=region)
    cw.put_metric_alarm(
        AlarmName="EC2-" + instanceId,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=2,
        MetricName=metric,
        Namespace="AWS/EC2",
        Period=60,
        Statistic='Average',
        Threshold=threshold,
        ActionsEnabled=True,
        OKActions=[
            topicArn,
        ],
        AlarmActions=[
            topicArn,
        ],
        AlarmDescription= metric + ' exceeded ' + threshold + ' for ' + instanceId,
        Dimensions=[
            {
                'Name' : "InstanceId",
                'Value' : instanceId
            },
        ],
        Unit=unit
    )

def lambda_handler(event, context):
    #ec2 = boto3.client('ec2')
    #regions = ec2.describe_regions()
    #for item in regions['Regions'] :
    #    region = item['RegionName']
    for region in ['us-east-1']:
        print(region)
        ssm = boto3.client(service_name='ssm', region_name=region)
        ec2region = boto3.client(service_name='ec2' , region_name=region)
        rds = boto3.client(service_name='rds' , region_name=region)
        elb = boto3.client(service_name='elbv2' , region_name=region)
        try:
            print("ec2")
            EC2Alarms = ssm.get_parameter(Name='EC2Alarms', WithDecryption=False)['Parameter']['Value']
            print(EC2Alarms)
            ec2instances = ec2region.describe_instances()
            for reservation in ec2instances['Reservations']:
                for instance in reservation['Instances']:
                    instanceId = instance['InstanceId']
                    for alarm in EC2Alarms.split(','):
                        metric, unit, threshold = alarm.split('=')
                        print(region, instanceId, unit, metric, threshold, topicArn)
                        #putEC2Alarm(region, instanceId, unit, metric, threshold, topicArn)
        except:
            pass
        try:
            print("ebs")
            EBSAlarms = ssm.get_parameter(Name='EBSAlarms' , WithDecryption=False)['Parameter']['Value']
            ec2vols = ec2region.describe_volumes()
            for vol in ec2vols['Volumes'] :
                for attachment in vol['Attachments'] :
                    volumeId = attachment['VolumeId']
                    for alarm in EBSAlarms.split(",") :
                        metric , unit , threshold = alarm.split('=')
                        print(region , volumeId , unit , metric , threshold , topicArn)
                        # putEBSAlarm(region, volumeId, unit, metric, threshold, topicArn)
        except:
            pass
        try:
            RDSAlarms = ssm.get_parameter(Name='RDSAlarms' , WithDecryption=False)['Parameter']['Value']
            dbs = rds.describe_db_instances()
            for db in dbs['DBInstances'] :
                dbInstanceId = db['DBInstanceIdentifier']
                for alarm in RDSAlarms.split(',') :
                    metric , unit , threshold = alarm.split('=')
                    print(region , dbInstanceId , unit , metric , threshold , topicArn)
                    # putRDSAlarm(region, dbInstanceId, unit, metric, threshold, topicArn)
        except:
            pass
        try:
            ALBAlarms = ssm.get_parameter(Name='ALBAlarms' , WithDecryption=False)['Parameter']['Value']
            lbs = elb.describe_load_balancers()
            for lb in lbs['LoadBalancers']:
                listParts = lb['LoadBalancerArn'].split("/")[1:4]
                lbId = "/".join(listParts)
                for alarm in ALBAlarms.split(","):
                    metric , unit , threshold = alarm.split('=')
                    print(region, lbId , unit , metric , threshold , topicArn)
                    #putALBAlarm(region, lbId, unit, metric, threshold, topicArn)
        except:
            pass
