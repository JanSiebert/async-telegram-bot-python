from AsyncTelegramBot import BotConversationLoop
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
loop = BotConversationLoop("API-TOKEN", conversationEntry)
signal.signal(signal.SIGINT, lambda _, __: loop.shutdown())
loop.enableDebug()
loop.startBotPolling()
