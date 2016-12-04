# Adapted from http://code.activestate.com/recipes/578668-encode-multipart-form-data-for-uploading-files-via/
import random

def toMultipartMessage(fields, files):
    def escape_quote(s):
        return s.replace(b'"', b'\\"')
    boundary = ''.join(random.choice("0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz") for i in range(30)).encode("ascii")
    __boundary = b'--' + boundary
    lines = []

    for name, value in fields.items():
        lines.extend((
            __boundary,
            b'Content-Disposition: form-data; name="' + escape_quote(name.encode("ascii")) + b'"',
            b'',
            value,
        ))

    for name, value in files.items():
        filename = value['filename']
        mimetype = value['mimetype'] if 'mimetype' in value else b'application/octet-stream'

        lines.extend((
            __boundary,
            b'Content-Disposition: form-data; name="'+escape_quote(name.encode("ascii"))+b'"; filename="'+escape_quote(filename)+b'"',
            b'Content-Type: ' + mimetype,
            b'',
            value['content'],
        ))

    lines.extend((
        __boundary + b'--',
        b'',
    ))
    body = b'\r\n'.join(lines)

    headers = {
        'Content-Type': 'multipart/form-data; boundary={0}'.format(boundary.decode("utf8")),
        'Content-Length': str(len(body)),
    }

    return (body, headers)
