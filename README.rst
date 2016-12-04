================
AsyncTelegramBot
================

Wrapper for Telegram`s Bot API utilizing asyncio

----------
How to use
----------

Here is how you could use it:

.. code:: python

    from AsyncTelegramBot import BotConversationLoop
    from random import randint
    import signal

    async def conversationEntry(I):
    	number = randint(1, 100)

    	await I.say("Can you guess my number between 1 and 100?")
    	while True:
    		answer = await I.gotAnswer()
    		if not answer.idsigit():
    			await I.say("Sorry, I did not understand.")
    			continue
    		if int(answer) > number:
    			await I.say("Good guess. But that is to high.")
    		elif int(answer) < number:
    			await I.say("My number is higher")
    		else:
    			await I.say("Correct!")
    			break
    loop = BotConversationLoop("YOUR-API-TOKEN", conversationEntry)
    signal.signal(signal.SIGINT, lambda _, __: loop.shutdown())
    loop.enableDebug()
    loop.startBotPolling()
