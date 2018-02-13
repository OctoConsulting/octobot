import boto3

lambda_client = boto3.client('lambda')


def lambda_handler(event, context):
    response = lambda_client.add_permission(
        Action='lambda:InvokeFunction',
        FunctionName='LexResponder',
        Principal='lex.amazonaws.com',
        # SourceAccount='123456789012',
        SourceArn='arn:aws:lex:us-east-1:749091557667:intent:*',
        StatementId='ID-3',
    )
    return 'Hello from Lambda'
