import boto3
import lexinterface as lx
import status
import qnamaker as qm
import string
import sys
from urllib.parse import urlparse

response_codes = [
    'Bot successfully built',
    'Bot already exists',
    'Creating intent table timed out'
]


def bot_name_from_url(url: str) -> str:
    """Makes a unique bot name from the base url from the base url and the
    path url.

    Args:
        url: A well-formed URL.

    Returns:
        The base url as a titlecased, no-space, no-puncutation string.
    """
    base_url = urlparse(url).netloc
    path = urlparse(url).path
    path_parts = path.split('/')[1:]  # [1:] because first is always empty
    path_hash = ''.join([pp[:2] for pp in path_parts])[
        :10]  # "hash" the rest of the url
    return convert_to_title(base_url + path_hash)


def convert_to_title(s: str) -> str:
    """Formats string as a title, such that the input string has no punctuation,
    is titlecased, and has no whitespace.

    Args:
        s: any string.

    Returns:
        The input string as a title.
    """
    # Remove punctuation
    s = s.translate(s.maketrans('', '', string.punctuation))
    s = s.title()
    # Remove whitespace
    s = s.translate(s.maketrans('', '', string.whitespace))
    return s


def main(event):
    faq_url = event['url']
    bot_name = bot_name_from_url(faq_url)
    table_name = bot_name + '_intents'

    # Check if already exists
    if status.get_bot_stage(bot_name) != 'DNE':
        return 1

    # Get intents from FAQ
    status.update_bot_stage(bot_name, 'EXTRACTING')
    api_key = qm.get_API_key()
    kbId = qm.create_knowledge_base(faq_url, api_key)
    intents = qm.download_knowledge_base(kbId, api_key)
    qm.delete_knowledge_base(kbId, api_key)

    # Save intents 
    status.update_bot_stage(bot_name, 'STORING')
    lx.create_dynamodb_table(table_name)
    if not lx.wait_until_table_ready(table_name, 20):
        return 2
    put_requests = [lx.put_request(bot_name, intent) for intent in intents]
    lx.iterate_batch_write_item(table_name, put_requests)

    # Create Lex intents and bot
    status.update_bot_stage(bot_name, 'BUILDING')
    intent_list = [{
        'intentName': bot_name + '_' + intent['name'],
        'intentVersion': '1'
    } for intent in intents]
    lx.create_intents(bot_name, intents)
    lx.create_intent_versions(intent_list)
    lx.create_bot(bot_name, intent_list)
    lx.create_bot_version(bot_name)

    # Publish bot
    status.update_bot_stage(bot_name, 'PUBLISHING')
    lx.create_bot_alias(bot_name, 100)
    
    # Done
    status.update_bot_stage(bot_name, 'READY')

    return 0

if __name__ == '__main__':
    if len(sys.argv) == 2:
        rcode = main({'url': sys.argv[1]})
        print(response_codes[rcode])
    else:
        print('Call must be of form "python3 main.py <url>"')

