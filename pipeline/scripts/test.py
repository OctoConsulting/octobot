import qnamaker as qna

faq_url = 'https://ramhacks.vcu.edu/'
api_key = qna.get_API_key()
kbId = qna.create_knowledge_base(faq_url, api_key)
kb_response = qna.download_knowledge_base(kbId, api_key)
print(kb_response)
qna.delete_knowledge_base(kbId, api_key)
