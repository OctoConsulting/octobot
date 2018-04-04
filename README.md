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

Let's take a detailed walkthrough of the process, from start to finish. If you are looking for more detailed developer documentation, look in the subfolders.
1. For this demo, we have a basic frontend in both web and in Android. A user inputs a URL to a web page with an FAQ. The app will then send a GET request to our API with the url as a query parameter.
2. The API is created using **AWS API Gateway**. There are three resources, `/create` , `/describe`  and `/delete`, for creating, describing, and deleting bots. There is currently no authentication or API key required to use these endpoints. When API Gateway receives a GET request, it will invoke an AWS Lambda function. For a `/create` GET request, the function **ProcessQueue** will be invoked with the query parameters passed in as part of the event object. For a `/describe` GET request, the function **DescribeBotStatus** will be invoked. And for a `/delete` GET request, the function **DeleteBot** will be invoked.
3. The **ProcessQueue** runs the pipeline `main.py` script on a running EC2 instance. The `main.py` runs through the entire pipeline. It will interact with a **Microsoft Azure** service to parse FAQ pages. An API key is required to use Microsoft Azure and that key is stored securely in an **S3 bucket**. Through a series of API calls, the pipeline scripts will feed Azure the FAQ url, download all the question-answer pairs that it parsed, and then delete the knowledge base from Azure. From here, we have the question and answers from the FAQ. We wrap these up and store them in a new **AWS DynamoDB** table, iteratively batch writing the intents into the table. Afterward, the scripts will interact with **AWS Lex**. Lex is the AWS chatbot service. To create a bot, you need intents to give it. And to create an intent, you need to provide sample utterances. The scripts create an intent for each question with the verbatim question text as a sample utterance. A bot is then created with those intents attached. All intents and the bot are built and an alias is applied to it. Right now, the Lex bot understands the different intents a user might express, but it does not know how to respond yet.
4. The generated Lex bot is configured to call a Lambda function called **LexResponder** whenever an intent is recognized. When LexResponder is invoked, it is sent the specific intent expressed by the user and the name of the bot the user is talking with. Using that information, it will look up the appropriate response in the DynamoDB table associated with that bot. The Lambda function will wrap up the response and send it back to the Lex bot and then to the user.
5. You can either chat the bot using AWS API calls to Lex or you can wrap the published Lex bot in a Twilio or Facebook service. This allows users to interact with the Lex bot on different platforms.

### How can I try it out?
Demo app download
URL to try
(screenshots)
