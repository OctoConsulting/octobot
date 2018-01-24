import boto3

def lambda_handler(event, context):
    client = boto3.client('lex-models')
    
    # TODO: split code off into functions as necessary
    
    # Add intents
    intent_names = []
    create_intent_responses = []
    for intent in event['intents']:
        # TODO: add exception handling to handle if intent already exists
        intent_names.append(event['bot_name'] + '_' + intent['name'])
        client.put_intent(
            name=intent_names[-1],
            sampleUtterances=intent['sample_utterances'],
            # TODO: change fulfillment activity to use LexResponder lambda function
            fulfillmentActivity={
                'type': 'CodeHook',
                'codeHook': {
                    'uri': 'arn:aws:lambda:us-east-1:749091557667:function:LexResponder',
                    'messageVersion': '$LATEST'
                }
            },
        )
        
    # TODO: add exception handling to handle if bot already exists
    # Create bot
    intent_objects = []
    for intent_name in intent_names:
        intent_objects.append({
            'intentName': intent_name,
            'intentVersion': '$LATEST'
        })
    create_bot_response = client.put_bot(
        name=event['bot_name'],
        intents=intent_objects,
        clarificationPrompt={
            'messages':[
                {
                    'contentType': 'PlainText',
                    'content': 'Sorry, can you repeat that?'
                }
            ],
            'maxAttempts': 3,
            'responseCard': 'Response card for clarificationPrompt'
        },
        abortStatement={
            'messages':[
                {
                    'contentType': 'PlainText',
                    'content': 'Sorry, I don\'t think I know how to help you.'
                }
            ],
            'responseCard': 'Response card for abortStatement'
        },
        idleSessionTTLInSeconds=123,
        voiceId='Kendra',
        locale='en-US',
        childDirected=False
        )
    
    # Combine output responses
    response_string = str(create_bot_response) + '\n\n'
    for create_intent_response in create_intent_responses:
        response_string += str(create_intent_response) + '\n\n'
    return response_string