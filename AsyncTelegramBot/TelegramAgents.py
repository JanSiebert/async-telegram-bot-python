from .AsyncHttp import request
from .Multipart import toMultipartMessage
import json
from asyncio import sleep

class TelegramSender:
	def __init__(self, token, loop):
		self._token = token
		self._loop = loop

	def _getUrl(self):
		return "https://api.telegram.org/bot{token}/sendMessage".format(token = self._token)

	def _getPhotoUrl(self):
		return "https://api.telegram.org/bot{token}/sendPhoto".format(token = self._token)

	def _getChatActionUrl(self):
		return "https://api.telegram.org/bot{token}/sendChatAction".format(token = self._token)

	async def sendChatAction(self, toChat, action):
		bodyContent = {'chat_id': toChat, 'action': action}
		bodyContent_raw = json.dumps(bodyContent).encode("utf8")
		headers = {'Accept': 'application/json', 'Content-type': 'application/json', 'Content-length': str(len(bodyContent_raw))}
		r = await request(self._getChatActionUrl(), method = "POST", header = headers, data = bodyContent_raw, loop = self._loop)
		return r.statusCode == 200

	async def sendMessage(self, toChat, text):
		bodyContent = {'chat_id': toChat, 'text': text}
		bodyContent_raw = json.dumps(bodyContent).encode("utf8")
		headers = {'Accept': 'application/json', 'Content-type': 'application/json', 'Content-length': str(len(bodyContent_raw))}
		r = await request(self._getUrl(), method = "POST", header = headers, data = bodyContent_raw, loop = self._loop)
		return r.statusCode == 200

	async def sendPhoto(self, toChat, binaryData, caption = None, mimetype = 'image/png'):
		bodyContent = {'chat_id': str(toChat).encode("utf8")}
		bodyFile = {'photo': {'filename': b'photo.png', 'mimetype': mimetype.encode('utf8'), 'content': binaryData}}

		if not caption is None:
			bodyContent['caption'] = caption.encode("utf8")

		body_raw, header = toMultipartMessage(bodyContent, bodyFile)
		headers = {'Accept': 'application/json', 'Content-type': header['Content-Type'], 'Content-length': header['Content-Length']}
		r = await request(self._getPhotoUrl(), method = "POST", header = headers, data = body_raw, loop = self._loop)
		return r.statusCode == 200

class TelegramUpdate:
	pass

class TelegramMessage(TelegramUpdate):
	def __init__(self):
		self.chatId = None
		self.chatType = None

		self.text = None
		self.fromFirstName = None
		self.fromLastName = None
		self.username = None
		self.fromId = None

def convertUpdateToMessage(upd):
	if not 'message' in upd:
		return None

	result = TelegramMessage()
	result.chatId = upd['message']['chat']['id']
	result.chatType = upd['message']['chat']['type']

	result.text = upd['message']['text']
	
	if 'from' in upd['message']:
		result.fromFirstName = upd['message']['from']['first_name'] if 'first_name' in upd['message']['from'] else None
		result.fromLastName = upd['message']['from']['last_name'] if 'last_name' in upd['message']['from'] else None
		result.fromId = upd['message']['from']['id'] if 'id' in upd['message']['from'] else None
		result.username = upd['message']['from']['username'] if 'username' in upd['message']['from'] else None

	return result


class TelegramUpdater:
	def __init__(self, token, loop):
		self._token = token
		self._cache = []
		self._updateId = None
		self._running = True
		self.timeoutInterval = 5
		self.maxSleep = 5
		self._loop = loop

	def _getUpdateUrl(self):
		raw = "https://api.telegram.org/bot{token}/getUpdates?timeout={timeout}{offset}".format(
				token = self._token,
				timeout = self.timeoutInterval,
				offset = "&offset=" + str(self._updateId) if not self._updateId is None else ""
			)
		return raw

	async def nextUpdate(self):
		if len(self._cache) > 0:
			return self._cache.pop(0)
		else:
			return await self._waitAndFetchLoop()

	def shutdown(self):
		self._running = False

	async def _waitAndFetchLoop(self):
		while self._running:
			await self._getUpdates()
			if len(self._cache) > 0:
				return self._cache.pop(0)
			else:
				await sleep(self.maxSleep, loop = self._loop)

	def _handleUpdate(self, upd):
		msg = convertUpdateToMessage(upd)
		if not msg is None:
			self._cache.append(msg)
		if 'update_id' in upd and (self._updateId is None or upd['update_id'] >= self._updateId):
			self._updateId = upd['update_id'] + 1

	def _parseResults(self, data):
		if not 'ok' in data:
			raise RuntimeError("Unknow format from telegram-api")

		if data['ok'] != True:
			raise RuntimeError("Oops. getUpdates() not okay")

		if not 'result' in data:
			return

		for update in data['result']:
			self._handleUpdate(update)

	async def _getUpdates(self):
		result = await request(url = self._getUpdateUrl(), loop = self._loop)
		js = json.loads(result.data.decode('utf8'))
		self._parseResults(js)
