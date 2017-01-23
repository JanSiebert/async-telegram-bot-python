import asyncio
import urllib.parse
import sys

class HttpResponseHeader:
    def __init__(self, header):
        self._header = header
    
    def _convertName(self, name):
        n = ""
        for c in name:
            if n and c.istitle():
                n += "-"
            n += c

        return n.upper()

    def __getattr__(self, name):
        name = self._convertName(name)
        if name in self._header:
            return self._header[name]
        else:
            return ""


class HttpResponse:
    def __init__(self, status, header, content):
        self.data = content
        self.header = HttpResponseHeader(header)
        self.status = status
        self.statusCode = status[0]
        self.statusText = status[1]


class HttpResponseParser:
	def __init__(self):
		self._headerCompleted = False
		self._rawBody = b""
		self.typeOf = None
		self.header = {}
		self.status = None

	def handleStatus(self, status):
		statusline = status.strip().decode("latin-1").split(' ', 3)
		if len(statusline) == 3:
			self.status = (int(statusline[1]), statusline[2])
		else:
			print(statusline)
			raise ValueError("HTTP Status expected: " + status.decode('latin-1').strip())

	def setContent(self, data):
		self._rawBody = data

	def addContent(self, data):
		self._rawBody += data

	def addHeaderLine(self, l):
		cleanedData = l.strip().decode("latin-1")
		if not cleanedData:
			self._headerCompleted = True
		else:
			try:
				key, value = cleanedData.split(':', 1)
			except ValueError:
				raise ValueError("Invalid HTTP-Header-Data: " + cleanedData)

			key = key.strip().upper()
			value = value.strip()
			if not key:
				raise ValueError("Invalid HTTP-Header-Data")

			self.header[key] = value

	def headerCompleted(self):
		return self._headerCompleted

def buildHeaderFromDict(d):
	dta = ''
	for key in d:
		dta += key + ': ' + d[key] + '\r\n'
	dta += '\r\n'
	return dta

async def request(url, method = 'GET', header = {}, data = None, loop = None):
    urlparts = urllib.parse.urlsplit(url)
    if urlparts.scheme == 'https':
        connect = asyncio.open_connection(urlparts.hostname, urlparts.port or 443, ssl=True, loop = loop)
    else:
        connect = asyncio.open_connection(urlparts.hostname, urlparts.port or 80, loop = loop)
    reader, writer = await connect
    query = ('{method} {path}{q} HTTP/1.1\r\n'
    	'Host: {hostname}\r\n'
    	'Connection: close\r\n' +
    	buildHeaderFromDict(header)).format(
    		method = method,
    		path = urlparts.path,
    		hostname = urlparts.hostname,
            q = "?" + urlparts.query if urlparts.query else ''
    	)
    writer.write(query.encode('latin-1'))
    
    if not data is None:
        writer.write(data)

    parser = HttpResponseParser()
    
    parser.handleStatus(await reader.readline())
    while not parser.headerCompleted():
        line = await reader.readline()
        if not line:
            break
        parser.addHeaderLine(line)
    
    if 'CONTENT-LENGTH' in parser.header:
    	leng = int(parser.header['CONTENT-LENGTH'])
    	parser.setContent(await reader.readexactly(leng))
    elif 'TRANSFER-ENCODING' in parser.header and parser.header['TRANSFER-ENCODING'].lower() == 'chunked':
    	while True:
    		line = await reader.readline()
    		if not line:
    			break
    		nextChunkSize = int(line.strip().split(b';',1)[0], 16)
    		if nextChunkSize != 0:
    			parser.addContent(await reader.readexactly(nextChunkSize))
    			await reader.readexactly(2)
    		else:
    			line = await reader.readline()
    			while line.strip() != b"":
    				line = await reader.readline()
    			break
    else:
    	raise RuntimeError("Unsupported HTTP mode")
    writer.close()
    
    if parser.headerCompleted():
        return HttpResponse(parser.status, parser.header, parser._rawBody)
    return None
