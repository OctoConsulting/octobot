import boto3

ddb_client = boto3.client('dynamodb', region_name='us-east-1')


def create_bot_stage_table():
    """Create table for storing bot stages if not exists.

    Returns:
        True if created. False if already exists.
    """
    try:
        ddb_client.create_table(
            TableName='octochat_bots',
            AttributeDefinitions=[
                {
                    'AttributeName': 'name',
                    'AttributeType': 'S'
                }
            ],
            KeySchema=[
                {
                    'AttributeName': 'name',
                    'KeyType': 'HASH'
                }
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
    except Exception as e:
        return False
    return True


def get_bot_stage(bot_name: str) -> str:
    """Get the current status of the bot in the DynamoDB tracker.

        Args:
            bot_name: The name of the bot.

        Returns:
        The status message stored in the DynamoDB table.
    """
    get_item_response = ddb_client.get_item(
        TableName='octochat_bots',
        Key={
            'name': {
                'S': bot_name
            }
        },
        AttributesToGet=[
            'stage'
        ]
    )
    if 'Item' in get_item_response and 'stage' in get_item_response['Item']:
        return get_item_response['Item']['stage']['S']
    return 'DNE'


def update_bot_faqurl(bot_name: str, new_faqurl: str) -> None:
    """Update the url of the bot in the DynamoDB tracker.

    Args:
        bot_name: The name of the bot.
        new_faqurl: The new url of the bot.
    """
    ddb_client.update_item(
        TableName='octochat_bots',
        Key={
            'name': {
                'S': bot_name
            }
        },
        UpdateExpression='set faqurl = :s',
        ExpressionAttributeValues={
            ':s': {
                'S': new_faqurl
            }
        }
    )

def update_bot_stage(bot_name: str, new_stage: str) -> None:
    """Update the status of the bot in the DynamoDB tracker.

    Args:
        bot_name: The name of the bot.
        new_stage: The new status of the bot.
    """
    try:
        ddb_client.update_item(
            TableName='octochat_bots',
            Key={
                'name': {
                    'S': bot_name
                }
            },
            UpdateExpression='set stage = :s',
            ExpressionAttributeValues={
                ':s': {
                    'S': new_stage
                }
            }
        )
    except Exception as e:
        pass


def delete_bot(bot_name: str):
    """Deletes bot from DynamoDB tracker, but not Lex.

    Args:
        bot_name: The name of the bot.
    """
    try:
        ddb_client.delete_item(
            TableName='octochat_bots',
            Key={
                'name': {
                    'S': bot_name
                }
            }
        )
    except Exception as e:
        pass
