import json

def encode(data):
    return repr(data)

def decode(stream):
    return eval(stream, None, {'null':None})
