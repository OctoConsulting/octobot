import boto3
import json

ssm_client = boto3.client('ssm')


def lambda_handler(event, context):
    print(event)
    response_package = {
        'isBase64Encoded': 'false',
        'statusCode': 200,
        'headers': {},
        'body': '{}'
    }

    if 'queryStringParameters' not in event:
        response_package['statusCode'] = 401
        return response_package
    if 'url' not in event['queryStringParameters']:
        response_package['statusCode'] = 401
        return response_package

    faq_url = event['queryStringParameters']['url']

    try:
        ssm_client.send_command(
            Targets=[
                {
                    'Key': 'tag:Name',
                    'Values': ['octochat-processor-1']
                }
            ],
            DocumentName='AWS-RunShellScript',
            TimeoutSeconds=1000,
            Parameters={
                'workingDirectory': [''],
                'executionTimeout': ['3600'],
                'commands': ['cd /home/ec2-user/octobot/pipeline/scripts/',
                             'python3 delete.py %s' % (faq_url)]
            },
            OutputS3BucketName='octochat-processor',
            MaxConcurrency='50',
            MaxErrors='0'
        )
    except Exception as e:
        print(e)
        response_package['statusCode'] = 402
    return response_package
