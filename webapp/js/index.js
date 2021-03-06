const converter = new showdown.Converter();

const enableChat = () => {
	$('#message-input').prop('disabled', false);
	$('#message-submit').prop('disabled', false);
	$('#chat-input').css('opacity', '1');
}

const log = (message) => {
	const logContainer = $('#logs');
	logContainer.html(logContainer.html() + '<br>' + message);
}

const configureAWS = () => {
	AWS.config.update({ region: 'us-east-1' });
	AWS.config.credentials = new AWS.CognitoIdentityCredentials({ IdentityPoolId: 'us-east-1:1252432e-9cd3-479d-98e5-ea5a26878766' });
}

const createBot = (url) => {
	const lambda = new AWS.Lambda({ region: 'us-east-1', apiVersion: '2015-03-31' });
	const pullParams = {
		FunctionName: 'CreateAzureKnowledgeBase',
		InvocationType: 'RequestResponse',
		LogType: 'None',
		Payload: JSON.stringify({'url': url})
	};

	lambda.invoke(pullParams, function (err, data) {
		if (err) {
			log(err);
		} else {
			const pullResults = JSON.parse(data.Payload);
			const pullBody = JSON.parse(pullResults.body)
			console.log(pullBody);
			if (!pullBody['error_message']) {
				botName = pullBody['bot_name'].trim();
				log(data.Payload);
				$('#url-input').data('botName', botName);
				enableChatWhenReady(botName);
			} else {
				log(data.Payload);
			}
		}
	});
}

const enableChatWhenReady = (botName) => {
	let lex = new AWS.LexRuntime({ apiVersion: '2016-11-28' });
	const params = {
		botAlias: 'DEV',
		botName: botName,
		inputText: 'Hi',
		userId: 'demo-webapp-id',
	};
	log('Bot building...');
	var poll_lex = setInterval(function(){
		lex.postText(params, function (err, data) {
			if (err) {
				console.log(err.toString());
			} else {
				window.clearInterval(poll_lex);
				log('Bot ready...');
				enableChat();
			}
		});
	}, 3000);
}

const appendMessageToChat = (user, message) => {
	$('#chat-log-list').append('<li>' + converter.makeHtml(user + ': ' + message) + '</li>');
}


const messageLex = (botName, message) => {
	let lex = new AWS.LexRuntime({ apiVersion: '2016-11-28' });
	const params = {
		botAlias: 'DEV',
		botName: botName,
		inputText: message,
		userId: 'demo-webapp-id',
	};
	lex.postText(params, function (err, data) {
		if (err) {
			console.log(err, err.stack);
		} else {
			console.log(data);
			appendMessageToChat('Bot', data['message']);
		}
	});
}

$(document).ready(function () {
	configureAWS();

	$('#create-bot').submit(function (e) {
		e.preventDefault();
		$(this).find('input').prop('disabled', true);
		url = $(this).find('#url-input').val();
		createBot(url);
	});

	$('#message-submit').click(function (e) {
		let messageInput = $('#message-input');
		let message = messageInput.val();
		let botName = $('#url-input').data('botName');
		appendMessageToChat('You', message);
		if (message.trim() != '' && botName !== undefined) {
			messageInput.val('');
			messageLex(botName, message);
		}
	})
});