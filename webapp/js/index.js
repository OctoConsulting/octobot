const enableChat = () => {
	$('#message-input').prop('disabled', false);
	$('#message-submit').prop('disabled', false);
	$('#chat-log').css('background', '#fff');
	$('#chat-log-list li').css('border-bottom', 'solid 1px #e0e0e0');
}

$(document).ready(function () {
	AWS.config.update({ region: 'us-east-1' });
	AWS.config.credentials = new AWS.CognitoIdentityCredentials({ IdentityPoolId: 'us-east-1:1252432e-9cd3-479d-98e5-ea5a26878766' });

	var lambda = new AWS.Lambda({ region: 'us-east-1', apiVersion: '2015-03-31' });
	var pullParams = {
		FunctionName: 'CreateAzureKnowledgeBase',
		InvocationType: 'RequestResponse',
		LogType: 'None',
	};

	var lex = new AWS.LexRuntime({ apiVersion: '2016-11-28' });

	let botName = '';//'Ramhacksvcuedu';

	$('#create-bot').submit(function (e) {
		e.preventDefault();
		$(this).children('input').prop('disabled', true);
		url = $(this).children('#url-input').val();
		pullParams['Payload'] = JSON.stringify({
			'url': url
		});
		lambda.invoke(pullParams, function (err, data) {
			if (err) {
				$('#logs').html($('#logs').html() + err);
			} else {
				pullResults = JSON.parse(data.Payload);
				console.log(pullResults)
				if(pullResults['succeeded']) {
					botName = pullResults['bot_name'].trim();
					$('#logs').html($('#logs').html() + '<br>' + data.Payload);
					$('#url-input').data('botName', botName);
					enableChat();
				} else {
					$('#logs').html($('#logs').html() + data.Payload);
				}
			}
		});
	});

	$('#message-submit').click(function (e) {
		let messageInput = $('#message-input');
		let message = messageInput.val();
		$('#chat-log-list').append('<li>' + 'You: ' + message + '</li>'); 
		if(message.trim() == '') return;
		messageInput.val('');
		var params = {
			botAlias: 'DEV', /* required */
			botName: $('#url-input').data('botName'), /* required */
			inputText: message, /* required */
			userId: 'demo-webapp-id', /* required */
		};
		lex.postText(params, function (err, data) {
			if (err) {
				console.log(err, err.stack); // an error occurred
			} else {
				console.log(data);
				$('#chat-log-list').append('<li>' + 'Bot: ' + data['message'] + '</li>');           // successful response
			}
		});
	})
});