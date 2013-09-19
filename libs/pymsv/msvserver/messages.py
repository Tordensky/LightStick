# Written by Ingar Arntzen, Motion Corporation
DEBUG=False


# MSV Commands
class MsvCmd:
    CREATE = 1 # create msvs in set
    GET = 2 # get msv states
    UPDATE = 3 # update msv in set
    DELETE = 4 # delete msvs
    PING = 5 # ping from client 
    PONG = 6 # pong to client
    UNSUB = 7 # remove subscription for msv

# Message Types
class MsgType:
    MESSAGE = 1
    REQUEST = 2
    RESPONSE = 3
    EVENT = 4


##############################################
# MESSAGES
##############################################

def msg_CREATE(msv_data_list, tunnel="optional"):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.CREATE,
        'tunnel': tunnel,
        'data': msv_data_list
        }

def msg_GET(msvid_list, tunnel="optional"):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.GET,
        'tunnel': tunnel,
        'data': msvid_list
        }

def msg_UPDATE(msv_data_list):
    return {
        'type': MsgType.MESSAGE,
        'cmd': MsvCmd.UPDATE,
        'data': msv_data_list
        }

def msg_DELETE(msvid_list, tunnel="optional"):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.DELETE,
        'tunnel': tunnel,
        'data': msvid_list
        }


def msg_CREATE_SINGLE(range, vector=None):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.CREATE,
        'tunnel': "optional",
        'data': [{
                'range': range,
                'vector': vector,
                }]
        }
    
def msg_UPDATE_SINGLE(msvid, vector):
    return {
        'type': MsgType.MESSAGE,
        'cmd': MsvCmd.UPDATE,
        'data': [{
                'msvid': msvid,
                'vector': vector
                }]
        }
    
def msg_RELATIVE_UPDATE_SINGLE(msvid, vector):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.UPDATE,
        'data': [{
                'msvid': msvid,
                'relative': True,
                'vector': vector
                }]
        }

def msg_GET_SINGLE(msvid):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.GET,
        'tunnel': "optional",
        'data': [msvid]
        }

def msg_DELETE_SINGLE(msvid):
    return {
        'type': MsgType.REQUEST,
        'cmd': MsvCmd.DELETE,
        'tunnel': "optional",
        'data': [msvid]
        }


##############################################
#  CREATE LISTEN PORT
##############################################

def create_listen_port(port=None, ipv6=True):
    # Create listening socket
    sock = None
    sa = None
    host = None if not ipv6 else '::'
    sock_family = socket.AF_INET if not ipv6 else socket.AF_UNSPEC
    for res in socket.getaddrinfo(host, 
                                  port,
                                  sock_family,
                                  socket.SOCK_STREAM, 
                                  0,
                                  socket.AI_PASSIVE):
        
        af, socktype, proto, canonname, sa = res
        sock = socket.socket(af, socktype, proto)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(sa)
        sock.listen(5)
        serv_addr = sock.getsockname()
        break
    return sock, serv_addr


##############################################
# PORTS
##############################################

RELAY_ACCEPT_PORT = 8090 # used by msv frontends
CLIENT_ACCEPT_PORT = 8091 # used by clients

##############################################
# RELAY PROTOCOL
##############################################

"""This implements utilities for the message protocol used between
Backend and Frontend.  Messages are constructed from a fixed size
header (4bytes) carrying payload len, followed by payload"""

import struct

HEADER_LEN = 4
FMT = "!I" # 4 byte unsigned integer

def relay_parse(data):
    """Parse one message from string data. 
    Returns the payload and possibly redundant data.
    Returns nothing if no complete message is available"""
    if DEBUG: print "Parsing RELAY data"
    if len(data) < HEADER_LEN:
        return None, data
    payload_end_offset = HEADER_LEN + struct.unpack(FMT, data[0:HEADER_LEN])[0]
    if len(data) < payload_end_offset:
        return None, data
    return data[HEADER_LEN:payload_end_offset], data[payload_end_offset:]

def relay_serialize(payload):
    """Serialize a single message."""
    return struct.pack(FMT, len(payload)) + payload


##############################################
# UTIL
##############################################

def string_to_float(_str, default):
    """Convert string to float."""
    if _str:
        try:
            return float(_str)
        except ValueError:
            pass
    return default

def string_to_int(_str, default):
    """Convert string to int"""
    if _str:
        try:
            return int(_str)
        except ValueError:
            pass
    return default

def queries_get_all(queries, key):
    """queries is response from urlparse.parse_qs(url.query)"""
    return queries.get(key, [])

def queries_get_first(queries, key):
    """queries is response from urlparse.parse_qs(url.query)"""
    all_queries = queries_get_all(queries, key)
    if len(all_queries) > 0: 
        return all_queries[0]


##############################################
# SERIALISE HTTP MESSAGE
##############################################

DELIMITER = '\r\n\r\n'

def _make_http_request_startline(verb, path, http_version):
    return "%s %s %s" % (verb, path, http_version)

def _make_http_response_startline(http_version, code, message):
    return "%s %d %s" % (http_version, code, message)

def make_http_response(code, message, 
                       headers=None, body="", http_version="HTTP/1.1"):
    start_line = _make_http_response_startline(http_version, code, message)
    if headers == None:
        headers = {}
    return http_serialize(start_line, headers, body=body)

def make_http_request(method, path, 
                      headers=None, body="", http_version="HTTP/1.1"):
    start_line = _make_http_request_startline(method, path, http_version)
    if headers == None:
        headers = {}
    return http_serialize(start_line, headers, body=body)

def http_serialize(start_line, headers, body=""):
    res = [start_line + "\r\n"]
    if headers.has_key('content-length'):
        del headers['content-length']
    for name, value in headers.items():
        res.append("%s: %s\r\n" % (name, value))
    res.append('content-length: %d\r\n' % len(body))
    res.append('\r\n')
    if body:
        res.append(body)
    return "".join(res)



##############################################
# PARSE HTTP MESSAGE
##############################################

def http_parse(data):
    """Try to parse a http message from data. Returns 
    (header, body) and possibly redundant data."""
    if DEBUG: print "Parsing HTTP data"
    tokens = data.split(DELIMITER, 1)
    if len(tokens) != 2:
        return (None, data) # No header
    header_map = parse_http_header(tokens[0])
    body_offset = len(tokens[0]) + len(DELIMITER)
    body_length = _get_content_length(header_map)
    message_length = body_offset + body_length
    if len(data) < message_length:
        return (None, data) # Incomplete body
    body = data[body_offset:message_length]
    return ((header_map, body), data[message_length:])

def parse_http_header(header):
    """Parse HTTP header."""
    lines = header.split('\n')
    if not lines: 
        return
    header_map = {'start_line':lines[0]}
    # Parse Initial Line
    tokens = lines[0].split(' ', 2)
    if len(tokens) != 3:
        return
    tokens = [token.strip() for token in tokens]
    if tokens[0].startswith("HTTP"):
        # response line
        header_map['version'] = tokens[0]
        header_map['code'] = string_to_int(tokens[1], -1)
        header_map['message'] = tokens[2]
    else:
        # request line  
        header_map['method'] = tokens[0]
        header_map['path'] = tokens[1]
        header_map['version'] = tokens[2]
    # Parse Header Lines
    for line in lines[1:]:            
        if len(line.strip()) > 0:
            tokens = line.split(":", 1)
            if len(tokens) == 2:
                header_map[tokens[0].lower()] = tokens[1].strip()
    return header_map

def _get_content_length(parsed_header):
    cl = parsed_header.get('content-length', None)
    return int(cl) if cl != None else 0





##############################################
# WEBSOCKET PROTOCOL
##############################################

"""This implements utilities for the web socket protocol used between
Frontend and Clients."""


import socket
import errno
import struct
import os
import uuid
import base64
import hashlib

class WS:
    WEB_SOCKET_MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

    # websocket supported version.
    VERSION = 13

    # operation code values.
    OPCODE_TEXT   = 0x1
    OPCODE_BINARY = 0x2
    OPCODE_CLOSE  = 0x8
    OPCODE_PING   = 0x9
    OPCODE_PONG   = 0xa

    # available operation code value tuple
    OPCODES = (OPCODE_TEXT, OPCODE_BINARY, OPCODE_CLOSE,
               OPCODE_PING, OPCODE_PONG)

    # opcode human readable string
    OPCODE_MAP = {
        OPCODE_TEXT: "text",
        OPCODE_BINARY: "binary",
        OPCODE_CLOSE: "close",
        OPCODE_PING: "ping",
        OPCODE_PONG: "pong"
        }

    # closing frame status codes.
    STATUS_NORMAL = 1000
    STATUS_GOING_AWAY = 1001
    STATUS_PROTOCOL_ERROR = 1002
    STATUS_UNSUPPORTED_DATA_TYPE = 1003
    STATUS_STATUS_NOT_AVAILABLE = 1005
    STATUS_ABNORMAL_CLOSED = 1006
    STATUS_INVALID_PAYLOAD = 1007
    STATUS_POLICY_VIOLATION = 1008
    STATUS_MESSAGE_TOO_BIG = 1009
    STATUS_INVALID_EXTENSION = 1010
    STATUS_UNEXPECTED_CONDITION = 1011
    STATUS_TLS_HANDSHAKE_ERROR = 1015

    STATUS_MAP = {
        STATUS_NORMAL : "Status Normal",
        STATUS_GOING_AWAY: "Status Going Away",
        STATUS_PROTOCOL_ERROR: "Status Protocol Error",
        STATUS_UNSUPPORTED_DATA_TYPE: "Status Unsupported Data Type",
        STATUS_STATUS_NOT_AVAILABLE: "Status Not Available",
        STATUS_ABNORMAL_CLOSED: "Status Abnormal Closed",
        STATUS_INVALID_PAYLOAD: "Status Invalid Payload",
        STATUS_POLICY_VIOLATION: "Status Policy Violation",
        STATUS_MESSAGE_TOO_BIG : "Status Message Too Big",
        STATUS_INVALID_EXTENSION: "Status Invalid Extension", 
        STATUS_UNEXPECTED_CONDITION : "Status Unexpected Condition",
        STATUS_TLS_HANDSHAKE_ERROR : "Status Handshake Error",
        }


    # data length threashold.
    LENGTH_7  = 0x7d
    LENGTH_16 = 1 << 16
    LENGTH_63 = 1 << 63

def _mask(mask_key, data):
    """
    mask or unmask data. Just do xor for each byte
    mask_key: 4 byte string(byte).        
    data: data to mask/unmask.
    """
    _m = map(ord, mask_key)
    _d = map(ord, data)
    for i in range(len(_d)):
        _d[i] ^= _m[i % 4]
    s = map(chr, _d)
    return "".join(s)

def generate_masking_key():
    """Make 4 byte random masking key"""
    return os.urandom(4)

def _create_ws_key():
    uid = uuid.uuid4()
    return base64.encodestring(uid.bytes).strip()

def _verify_ws_key_response(ws_key, ws_key_response):
    key_response = _generate_ws_key_response(ws_key)
    return key_response == ws_key_response

def _generate_ws_key_response(ws_key):
    the_string = ws_key + WS.WEB_SOCKET_MAGIC
    m = hashlib.sha1()
    m.update(the_string)
    return base64.b64encode(m.digest())

def make_ws_request_headers(server_addr):
    headers = {}
    headers['upgrade'] = 'websocket'
    headers['connection'] = 'upgrade'        
    headers['host'] = "%s:%d" % server_addr        
    headers['origin'] = "%s:%d" % server_addr
    headers['sec-websocket-key'] = _create_ws_key()
    headers['sec-websocket-protocol'] = "chat, superchat"
    headers['sec-websocket-version'] = WS.VERSION
    return headers

def verify_ws_request_headers(headers):
    if not headers.has_key("sec-websocket-key"):
        print "No sec key"
        return False
    upgrade = headers.get("upgrade", "").lower()
    connection = headers.get("connection", "").lower()
    connection_tokens = [x.strip() for x in connection.split(',')]
    if upgrade == "websocket" and "upgrade" in connection_tokens:
        return True
    return False

def make_ws_response_headers(request_headers):
    reply_headers = {}
    if "cookie" in request_headers.keys():
        reply_headers["cookie"] = request_headers["cookie"]
    reply_headers["connection"] = "upgrade"
    reply_headers["upgrade"] = "websocket"
    reply_headers["sec-websocket-version"] = WS.VERSION
    ws_key = request_headers["sec-websocket-key"]
    ws_key_response = _generate_ws_key_response(ws_key)
    reply_headers["sec-websocket-accept"] = ws_key_response
    return reply_headers

def verify_ws_response_headers(ws_key, headers):
    upgrade = headers.get("upgrade", "").lower()
    connection = headers.get("connection", "").lower()
    if upgrade != "websocket" or connection != "upgrade":
        return False
    ws_key_response = headers.get("sec-websocket-accept", None)
    if not ws_key_response:
        return False
    return _verify_ws_key_response(ws_key, ws_key_response)



##############################################
# PARSE WEBSOCKET FRAME
##############################################
        
def ws_parse(data):
    """Parse a web socket frame from string data. 
    Returns the payload and possibly redundant data."""
    if DEBUG:
        print "Parsing WS data"
    data_len = len(data)
    if data_len < 4:
        if DEBUG: print "Incomplete header"
        return (None, data) # Incomplete header
    # Parse data
    bits = struct.unpack("!Bccc", data[0:4])[0]
    fin = bits & 0b10000000 # Store but ignore
    opcode = bits & 0b00001111
    # Size
    i = struct.unpack("!I", data[0:4])[0]
    size = (i>>16) & 0b1111111
    size_end_index = 2
    if size == 126:
        size = struct.unpack("!H", data[2:4])[0]
        size_end_index = 4
    elif size == 127:
        if data_len < 10:
            if DEBUG: print "Incomplete header, size %d, data_len %d"%(size, data_len)
            return (None, data) # Incomplete header
        size = struct.unpack("!Q", data[2:10])[0]
        size_end_index = 10
    # Masking key
    masked = (i >> 23) & 1 
    if masked: 
        mask_end_index = size_end_index+4
        if data_len < mask_end_index:
            return (None, data) # Incomplete header
        masking_key = data[size_end_index:mask_end_index]
    else:
        masking_key = None
        mask_end_index = size_end_index
    
    if DEBUG: 
        print "fin: %s opcode: %s size: %d masked: %s, mask_key: %s"%\
            (fin, opcode, size, masked, masking_key)
    payload_end_index = mask_end_index + size
    if data_len < payload_end_index:
        if DEBUG: print "Incomplete payload"
        return (None, data) # Incomplete payload
    # Unmask
    payload = data[mask_end_index:payload_end_index] 
    if masking_key:
        payload = _mask(masking_key, payload)
    # Return result
    msg = {
        'fin': fin,
        'opcode': opcode,
        'masked': masked,
        'payload': payload
        }
    if DEBUG: print msg
    return msg, data[payload_end_index:] # payload, more data



##############################################
# SERIALIZE WEBSOCKET FRAME
##############################################

def ws_serialize(payload, opcode=1, fin=1, mask=False):
    """Serialize a string payload to a web socket frame."""
    if not payload:
	    return None
    size = len(payload)
    data = chr((fin << 7) | opcode)
    if size < 126:
	    data += chr((mask << 7)|size)
    elif size < 65535:
	    data += chr((mask << 7)| 0x7e)
	    data += struct.pack("!H", size)
    else:
	    data += chr((mask << 7)| 0x7f)
	    data += struct.pack("!Q", size)
    if opcode==1 and payload.__class__ == type(u''):
	    payload = payload.encode("utf8")

    if DEBUG:
        print "OUT: fin: %s opcode: %s size: %d masked: %s"%\
            (fin, opcode, size, mask)
    # mask payload
    if mask:
        masking_key = generate_masking_key()
        payload = _mask(masking_key, payload)
        return data + masking_key + payload
    else:
        return data + payload
