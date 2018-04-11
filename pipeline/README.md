# Documentation

Below includes documentation and dicussion for

1. API Gateway
2. Lambda
3. IAM
4. Architecture
5. To-dos



## 1. API Resources

These endpoints are for interacting with the octobot pipeline. 

### Create

Create a bot if it does not exist already.

**Request URL**

```http
GET https://5is22k69ye.execute-api.us-east-1.amazonaws.com/v1/create?url=<url>
```

**Response**

```json
{
    "bot_name": "Ramhacksvcuedu"
}
```

*If you are creating a demo app, you can poll the status of the bot throughout the bot creation process.*

### Describe

Describe the status of a bot.

**Request URL**

```http
GET https://5is22k69ye.execute-api.us-east-1.amazonaws.com/v1/describe?url=<url>
```

**Response**

```json
{
    "bot_name": "Ramhacksvcuedu",
    "status": "READY"
}
```

`status` can take on the following values:

* `DNE` if the bot does not exist
* `EXTRACTING` if the question-answer pairs are being extracted using the Azure QnAMaker interface
* `STORING` if the question-answer pairs are being stored in a DynamoDB table
* `BUILDING` if the Lex bot is being created
* `PUBLISHING` if the Lex bot is being published
* `READY` if the Lex bot is ready to interact
* `DELETING` if the Lex bot is in the process of being deleted

### Delete

Delete the bot.

**Request URL**

```http
GET https://5is22k69ye.execute-api.us-east-1.amazonaws.com/v1/delete?url=<url>
```

**Response**

```json
{}
```

*If you are creating a demo app, you can poll the status of the bot throughout the bot deletion process.*



## 2. Lambda

There are only a few necessary Lambda functions. Any functions you encounter in AWS that are not discussed below are legacy functions from the previous serverless architecture.

### ProcessQueue

Runs `main.py` in the EC2 instance to start the pipeline. Returns a response payload according to the guidelines imposed by AWS API Gateway. This function is invoked when the `/create` endpoint is accessed.

### DescribeBotStatus

Searches the DynamoDB table called `octochat_bots` for the existence and status of a bot. Returns a status, described in the API documentation for `/describe`.

### DeleteBot

Deletes the bot and associated metadata from Lex and DynamoDB. This function is invoked by the `/delete` endpoint.

### LexResponder

Looks up the defined response for an intent given the bot and intent names. The look up occurs in the bot's DynamoDB table that contains the question-answer pairs. This function is invoked when the Lex bot is interacting with a user and an intent is fulfilled.

### AddLambdaPermissionToLex

Adds the `lambda:InvokeFunction` permission to the LexResponder Lambda function. Only needs to be ran once.



## 3. IAM

Every Lambda function or EC2 instance requires permissions to interact with other AWS services. Every inline policy is for "Any" resource unless specified with a sub-bullet.

### AddLambdaPermissionToLexRole

**Attached to**

- AddLambdaPermissionToLex Lambda function

**Default Policy**

- lambda_basic_execution

**Inline Policies**

- lambda:AddPermission

### DeleteBotRole

**Attached to**

- DeleteBot Lambda function

**Default Policy**

- lambda_basic_execution

**Inline Policies**

- ssm:SendCommand

### DescribeBotStatusRole

**Attached to**

- DescribeBotStatus Lambda function

**Default Policy**

- lambda_basic_execution

**Inline Policies**

- dynamodb:GetItem

### LexResponderRole

**Attached to**

- LexResponder Lambda function

**Default Policy**

- lambda_basic_execution

**Inline Policies**

- dynamodb:GetItem
- lambda:InvokeFunction

### OctoChatEC2Role

**Attached to**

* EC2 instances

**Default Policy**

* AmazonEC2RoleforSSM

**Inline Policies**

* dynamodb:CreateTable
* dynamodb:BatchWriteItem
* dynamodb:PutItem
* dynamodb:DescribeTable
* dynamodb:DeleteItem
* dynamodb:GetItem
* dynamodb:Scan
* dynamodb:UpdateItem
* dynamodb:DeleteTable
* lex:DeleteBotAlias
* lex:DeleteBot
* lex:CreateBotVersion
* lex:DeleteIntent
* lex:PutIntent
* lex:DeleteIntentVersion
* lex:DeleteBotVersion
* lex:PutBotAlias
* lex:CreateIntentVersion
* lex:PutBot
* s3:GetObject
  * arn:aws:s3:::octochat-processor/secrets.yml

### ProcessQueueRole

**Attached to**

- ProcessQueue Lambda function

**Default Policy**

- lambda_basic_execution

**Inline Policies**

- ssm:SendCommand



## 4. Lambda vs. EC2

Here we will briefly discuss the rationale behind the choices of architecture design. Originally, we had the entire pipeline broken into smaller functions and set up as chained Lambda functions. Unfortunately, because of the size of some FAQ pages, some Lambda functions would time out, making that architecture not scalable. Although the serverless structure could still potentially work if the Lambda functions were broken down into smaller functions, it was easier to shift to a server setup with EC2. Currently, interactions with the API invoke small Lambda functions that use Systems Manager to run scripts on the EC2 instance.


## 5. To-dos
* Definitely should not have created a separate DynamoDB table for each new bot. Instead, there should just be one big table that contains all the intents for all bots with an extra column that indicates the bot. This will cut out a solid 30 to 60 seconds off the creation pipeline that were dedicated to just creating a new DynamoDB table.
