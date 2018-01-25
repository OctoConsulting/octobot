import boto3
import time

def lambda_handler(event, context):
	bot_name = event['bot_name']
	intents = event['intents']
	
	table_name = bot_name + '_intents'
	ddb_client = boto3.client('dynamodb')
	
	# TODO: add exception handling to create table if not exists
	create_table_response = ddb_client.create_table(
		TableName=table_name,
		KeySchema=[
			{
				'AttributeName': 'intent',
				'KeyType': 'HASH'
			},
			{
				'AttributeName': 'version',
				'KeyType': 'RANGE'
			}
		],
		AttributeDefinitions=[
			{
				'AttributeName': 'intent',
				'AttributeType': 'S'
			},
			{
				'AttributeName': 'version',
				'AttributeType': 'S'
			}
		],
		ProvisionedThroughput={
			'ReadCapacityUnits': 10,
			'WriteCapacityUnits': 10
		}
	)
	
	iteration_count = 0
	MAX_ITERATIONS_ALLOWED = 8
	while iteration_count < MAX_ITERATIONS_ALLOWED:
		# TODO: add error handling
		describe_table_response = ddb_client.describe_table(
			TableName=table_name
		)
		table_status = describe_table_response['Table']['TableStatus']
		if table_status == 'ACTIVE':
			break
		iteration_count += 1
		time.sleep(3)
	else:
		print('MAX_ITERATIONS_ALLOWED reached, table not active')
		return 'MAX_ITERATIONS_ALLOWED_ERROR'
	
	# TODO: make version reflect the correct version
	put_requests = [{
		'PutRequest': {
			'Item': {
				'intent': {
					'S': bot_name + '_' + intent['name']
				},
				'version': {
					'S': '$LATEST'
				},
				'response': {
					'S': intent['response']
				}
			}
		}
	} for intent in intents]
	batch_write_item_response = ddb_client.batch_write_item(
		RequestItems={
			table_name: put_requests
		}
	)

	return str(batch_write_item_response)
