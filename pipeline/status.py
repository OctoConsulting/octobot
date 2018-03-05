import boto3

ddb_client = boto3.client('dynamodb', region_name='us-east-1')

def update_bot_stage(bot_name: str, new_stage: str):
    """Update the status of the bot in the DynamoDB tracker.

    Args:
        bot_name: The name of the bot.
        new_stage: The new status of the bot.
    """
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


def delete_bot(bot_name: str):
    """Deletes bot from DynamoDB tracker, but not Lex.

    Args:
        bot_name: The name of the bot.
    """
    ddb_client.delete_item(
        TableName='octochat_bots',
        Key={
            'name': {
                'S': bot_name
            }
        }
    )
