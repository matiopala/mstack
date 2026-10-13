import json
from urllib.request import Request, urlopen


def send(url, event):
    request = Request(url, json.dumps(event).encode(),
                      {"Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=10) as response:
        return response.status
