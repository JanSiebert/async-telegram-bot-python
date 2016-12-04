import asyncio
from .TelegramAgents import TelegramUpdater, TelegramSender
from random import random

class IdentityProxy:
	def __init__(self, myId, loop, youName = None):
		self.myId = myId
		self.loop = loop
		self._youName = youName

	def getYourName(self):
		return self._youName
	
	async def say(self, txt):
		await self.loop.say(self.myId, txt)

	async def waitAndSay(self, txt):
		await self.waitRandom()
		await self.say(txt)

	async def sendPhoto(self, data, caption = None, mimetype = 'image/png'):
		await self.loop.sendPhoto(self.myId, data, caption, mimetype)

	def beginTyping(self):
		return self.loop.sendChatAction(self.myId, 'typing')

	def beginSendingPhoto(self):
		return self.loop.sendChatAction(self.myId, 'upload_photo')

	def gotAnswer(self):
		return self.loop.gotAnswer(self.myId)

	def wait(self, seconds):
		return asyncio.sleep(seconds, loop = self.loop)

	def waitRandom(self, seconds):
		return asyncio.sleep(0.5 + random() * 0.5, loop = self.loop)

	def __getattr__(self, name):
		return getattr(self.loop, name)

class Dummy:
	pass

def simplifyText(txt):
	return txt.replace("\n", " ")

def get_conversation_manager(token, conversationEntry, loop = None):
	return BotConversationLoop(loop or asyncio.get_event_loop(), token, conversationEntry)

class BotConversationLoop:
	def __init__(self, loop, token, conversationEntry):
		super().__init__()
		self._token = token
		self._conversationEntry = conversationEntry
		self._updateter = TelegramUpdater(token, loop)
		self._sender = TelegramSender(token, loop)
		self._loop = loop

		self._conversations = {}
		self._shouldContinue = True
		self._verbose = False

	def enableDebug(self):
		self._verbose = True

	async def sendPhoto(self, chatId, data, caption, mimetype):
		if self._verbose: print(chatId, ">> [ photo ]")
		if not await self._sender.sendPhoto(chatId, data, caption):
			self._removeConversation(chatId)

	async def say(self, chatId, txt):
		if self._verbose: print(chatId, ">> ", simplifyText(txt))
		if not await self._sender.sendMessage(chatId, txt):
			self._removeConversation(chatId)

	async def sendChatAction(self, chatId, action):
		if self._verbose: print(chatId, ">> [", simplifyText(action), "]")
		if not await self._sender.sendChatAction(chatId, action):
			self._removeConversation(chatId)

	def gotAnswer(self, chatId):
		self._conversations[chatId].waitForAnswer = self._loop.create_future()
		return self._conversations[chatId].waitForAnswer

	def shutdown(self):
		self._loop.call_soon_threadsafe(self._shutdown_threadsafe_entry)

	def _shutdown_threadsafe_entry(self):
		self._shouldContinue = False
		self._updateter.shutdown()
		
		for conversation in list(self._conversations.keys()):
			self._removeConversation(conversation)	

	def _removeConversation(self, chatId):
		if chatId in self._conversations:
			self._conversations[chatId].coro.cancel()
			del self._conversations[chatId]

	def _resumeTalk(self, chatId, text):
		if self._verbose: print(chatId, "<< ", simplifyText(text))
		self._conversations[chatId].waitForAnswer.set_result(text)

	def _waitingForAnswer(self, chatId):
		return (not self._conversations[chatId].waitForAnswer is None
			and not self._conversations[chatId].waitForAnswer.done())

	def _activeConversationExistsWithId(self, chatId):
		return chatId in self._conversations and not self._conversations[chatId].coro.done()

	def _handleUpdate(self, msg):
		if msg is None:
			return
		if self._activeConversationExistsWithId(msg.chatId):
			if self._waitingForAnswer(msg.chatId):
				if not msg.text is None:
					self._resumeTalk(msg.chatId, msg.text)
				else:
					if self._verbose: print(msg.chatId, "|| (unknown message)")
			else:
				if self._verbose: print(msg.chatId, "|| (message discarded)")
		else:
			if self._verbose: print(msg.chatId, "<< (new)")
			newI = IdentityProxy(msg.chatId, self, msg.fromFirstName or msg.username)
			newCoroutine = self._conversationEntry(newI)
			newConversation = Dummy()
			newConversation.identity = newI
			newConversation.coro = self._loop.create_task(newCoroutine)
			newConversation.waitForAnswer = None
			self._conversations[msg.chatId] = newConversation

	def startBotPolling(self, maxSleep = 5, maxTimeout = 5):
		self._updateter.maxSleep = maxSleep
		self._updateter.timeoutInterval = maxTimeout
		self._loop.run_until_complete(self.pollLoop())

	async def pollLoop(self):
		while self._shouldContinue:
			nextUpdate = await self._updateter.nextUpdate()
			self._handleUpdate(nextUpdate)
