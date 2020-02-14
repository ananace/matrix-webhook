#!/usr/bin/env python3
"""
Matrix Webhook
Post a message to a matrix room with a simple HTTP POST
"""

import asyncio
import json
import os

from aiohttp import web
from matrix_client.client import MatrixClient

SERVER_ADDRESS = ('', int(os.environ.get('PORT', 4785)))
MATRIX_URL = os.environ.get('MATRIX_URL', 'https://matrix.org')
MATRIX_ID = os.environ.get('MATRIX_ID', 'wwm')
MATRIX_PW = os.environ['MATRIX_PW']
API_KEY = os.environ['API_KEY']

client = MatrixClient(MATRIX_URL)
client.login(username=MATRIX_ID, password=MATRIX_PW)
rooms = client.get_rooms()


async def handler(request):
    """
    Coroutine given to the server, st. it knows what to do with an HTTP request.
    This one handles a POST, checks its content, and forwards it to the matrix room.
    """
    data = json.loads(request.read().decode())
    status, ret = 400, 'I need a json dict with text & key'
    if all(key in data for key in ['text', 'key']):
        status, ret = 401, 'I need the good "key"'
        if data['key'] == API_KEY:
            status, ret = 404, 'I need the id of the room as a path, and to be in this room'
            if request.rel_url[1:] not in rooms:
                # try to see if this room has been joined recently
                rooms = client.get_rooms()
            if request.rel_url[1:] in rooms:
                status, ret = 200, json.dumps(rooms[request.rel_url[1:]].send_text(data['text']))

    return web.Response(text='{"status": %i, "ret": "%a"}' % (status, ret),
                        content_type='application/json',
                        status=status)


async def main():
    server = web.Server(handler)
    runner = web.ServerRunner(server)
    await runner.setup()
    site = web.TCPSite(runner, *SERVER_ADDRESS)
    await site.start()

    print("======= Serving ======")

    # pause here for very long time by serving HTTP requests and
    # waiting for keyboard interruption
    await asyncio.sleep(100 * 3600)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
    loop.close()