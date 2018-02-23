# octobot
A full-length pipeline to generate chatbots from content sources

## The Problem
There are thousands upon thousands of calls made each day from people who are looking for basic help. Someone can call looking for help changing their password or looking up information in their account. For many, it is easier and much quicker to call a number and ask a representative rather than look through an entire website for the right help documentation. Handling these calls requires hundreds of people and millions of dollars. And importantly, the information callers are seeking is noncomplex and readily available.

Organizations have already flagged this as a potential area for improvement. As such, some are shifting to using chatbots to interact --- through voice or through text --- with those requesting help. These chatbots are great for understanding and responding to users, but they need to be trained first. And people are training them manually. This takes a long time and effort for every single bot you want to build.

## The Solution
We propose a pipeline to automatically generate a chatbot for given content repository. Not only will this pipeline save time and effort in answering people's questions, but it will also save time and effort in producing the chatbots necessary to answer those questions.

Currently, we're focusing on Frequently Asked Questions sections of websites because they are relatively structured and are directly related to call center type questions. Theoretically, one could analyze what questions their call centers answer and compile an FAQ from that. From there, our pipeline could read in that FAQ and spit back out a chatbot to answer those questions.

### What exactly are chatbots?
Chatbots utilize artificial intelligence to understand and respond to users. However, to do properly understand users, chatbots must be pretrained. Specifically, chatbots must be fed information about the different reasons a user might be talking with them (intents), the different ways a user might express the same intent (sample utterances), and the different types of values a user can mention e.g. location, phone numbers, time (slots).

### How are we building chatbots?
Our pipeline primarily uses Amazon Web Services (AWS) and Microsoft Azure. From a high-level, we use Microsoft Azure to parse FAQ webpages into question-answer pairs and then we use an AWS service called Lex to create, build, and publish our bot. From there, you can wrap the published bot into any platform e.g. Twilio, Facebook.

Let's take a detailed walkthrough of the process, from start to finish.
1. Frontend
2. API Gateway
3. Lambda
4. DynamoDB
5. Lex
6. Twilio
Go to the lambda folder for detailed dev notes on each function.

### How can I try it out?
Demo app download
URL to try
(screenshots)
