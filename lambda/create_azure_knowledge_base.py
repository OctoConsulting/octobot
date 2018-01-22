from urllib.request import Request, urlopen
import json
import boto3
import string
from time import asctime
import os
from base64 import b64decode

QNAMAKER_API_KEY = os.environ['qnamaker_api_key']

def remove_invalid_punctuation(s):
    """Return the input string without invalid punctuation to conform to Lex
    intent rules.
    
    Lex intents do not allow puncutation except apostrophes, underscores, and
    hyphens.
    """
    # Create string of invalid punctuation 
    invalid_punctuation = ''.join([ch for ch in string.punctuation if ch not in '-_\''])
    # Remove punctuation from string
    s = s.translate(s.maketrans('', '', invalid_punctuation))
    s = s.strip()
    return s
    

def convert_to_title(s):
    """Return the input string with title case, no punctuation, and no
    whitespace.
    
    This does not create the best titles, but this is a simple hack for now.
    """
    # Remove punctuation
    s = s.translate(s.maketrans('', '', string.punctuation))
    s = s.title()
    # Remove whitespace
    s = s.translate(s.maketrans('', '', string.whitespace))
    return s
    
def create_knowledge_base(faq_url):
    """Return response from create request to Azure QnAMaker.
    """
    create_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/create'
    create_request = Request(create_request_endpoint)
    create_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    create_request.add_header('Content-Type', 'application/json')
    # TODO: call crawler to get all faq urls if the user wants it to
    input_data = str.encode(str({
        'name': 'CAKB_' + convert_to_title(asctime()), # include the time of creation in the bot title for logging
        'urls': [
            faq_url
        ]
    }))
    create_response = urlopen(create_request, data=input_data, timeout=15).read().decode('utf-8')
    return create_response

def lambda_handler(event, context):
    # TODO: Check urlopen responses for success and deal with endpoint
    
    faq_url = event['url']
    
    create_response = create_knowledge_base(faq_url)
    create_response_json = json.loads(create_response)
    kbId = create_response_json['kbId'] # kb = knowledge base

    # Download the generated knowledge base
    download_kb_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/' + kbId
    download_kb_request = Request(download_kb_request_endpoint)
    download_kb_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    download_kb_response = urlopen(download_kb_request, timeout=15).read().decode('utf-8') # returns an address from which to download kb
    download_kb_link = download_kb_response[1:-1] #[1:-1] removes quotation marks from url
    kb_response = urlopen(download_kb_link).read().decode('utf-8-sig') # must be utf-8-sig to remove BOM characters
    
    # Format knowledge base to be readable
    lines = kb_response.split('\r')
    lines = lines[1:-1] # the first line are just headers; the last line is empty
    lines = [line.split('\t') for line in lines]
    
    # Generate a list of intent objects from the knowledge base
    intents = [{
            'name': convert_to_title(question),
            'sample_utterances': [remove_invalid_punctuation(question)],
            'response': answer
        } for question, answer, source in lines]
    
    # Assemble payload for CreateLexBot
    payload = {
        'bot_name': convert_to_title(faq_url),
        'intents': intents
    }
    
    # Invoke CreateLexBot
    lambda_client = boto3.client('lambda')
    create_lex_bot_response = ''
    try:
        create_lex_bot_response = lambda_client.invoke(
            FunctionName='CreateLexBot',
            InvocationType='RequestResponse',
            Payload=json.dumps(payload)
            )
    except Exception as e:
        raise e
        
    # Delete knowledge base after done with it
    delete_request_endpoint = 'https://westus.api.cognitive.microsoft.com/qnamaker/v2.0/knowledgebases/' + kbId
    delete_request = Request(delete_request_endpoint, method='DELETE')
    delete_request.add_header('Ocp-Apim-Subscription-Key', QNAMAKER_API_KEY)
    delete_response = urlopen(delete_request, timeout=15).read().decode('utf-8')
    print(str(delete_response))
    
    # TODO: parse response to pass through responses
    return str(create_lex_bot_response)