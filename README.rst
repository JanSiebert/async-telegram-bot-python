================
AsyncTelegramBot
================

Wrapper for Telegram`s Bot API utilizing asyncio. It does **not** support all methods the Telegram API provides. It is designed for conversations with a single user. It does **only** support recieving texts (yet) and does **only** support sending text and photos.

-------
Example
-------

Here is how you could use it:

.. code:: python

    from AsyncTelegramBot import get_conversation_manager
    from random import randint
    import signal

    async def conversationEntry(I):
        number = randint(1, 100)

        await I.say("Can you guess my number between 1 and 100?")
        while True:
            answer = await I.gotAnswer()
            if not answer.isdigit():
                await I.say("Sorry, I did not understand.")
                continue
            if int(answer) > number:
                await I.say("Good guess. But that is to high.")
            elif int(answer) < number:
                await I.say("My number is higher")
            else:
                await I.say("Correct!")
                break
    loop = get_conversation_manager("YOUR-API-TOKEN", conversationEntry)
    signal.signal(signal.SIGINT, lambda _, __: loop.shutdown())
    loop.enableDebug()
    loop.startBotPolling()

---------------
What *I* can do
---------------

The following functions can be *awaited*

say(text)
    Send *text* to the user
wait(n)
    Wait *n* seconds
sendPhoto(data, caption = None, mime = 'image/png')
    Send image, binary encoded in *data*, to the user.
beginTyping()
    Send typing-indicator
beginSendingPhoto()
    Send sending-photo-indicator
gotAnswer()
    Returns with text from the user

You can get the user`s name by calling *getYourName()*.