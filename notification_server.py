"""
    Notification Server
    This module has the web and websocket server code
"""

import os
import pathlib
import signal
import asyncio
import json
import logging
import argparse
import socketio
from aiohttp import web

class NotificationServer():
    """This module does blah blah."""

    def __init__(self, logging):
        self.log = logging
        self.script_dir = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
        self.registered_codes = {}
        self.sio = socketio.AsyncServer(logger=True, engineio_logger=True)
        self.app = web.Application()
        self.app.on_shutdown.append(self.on_shutdown)
        self.routes = [
            web.get("/", self.index),
            web.get("/favicon.ico", self.static_file),
            web.get("/example.html", self.static_file),
            web.get("/notify", self.notify),
            web.get("/sources/{tail:.*}", self.static_file)
        ]
        # event handler = ["event name", handler_function, Namespace=None]
        self.event_handlers = [
            ["connect", self.connect, None],
            ["disconnect", self.disconnect, None],
            ["REGISTER", self.register, None],
            ["*", self.event, None]
        ]
        # Register WebApp Routes
        self.app.add_routes(self.routes)
        # Register SIO Event Callbacks
        for handler in self.event_handlers:
            self.sio.on(handler[0], handler[1], handler[2])
        self.sio.attach(self.app)
        self._loop = None
        # Setup the SIGTERM Handler to gracefully exit (hopefully)
        signal.signal(signal.SIGTERM, self.sig_handler)
        signal.signal(signal.SIGINT, self.sig_handler)

    async def index(self, request=web.Request): # pylint: disable=unused-argument
        """Serve Index"""
        with open('static/test.html', "r", encoding="utf8") as f:
            return web.Response(text=f.read(), content_type='text/html')
    
    async def client(self, request=web.Request): # pylint: disable=unused-argument
        """Serve client.html for testing"""
        with open('example/client.html', "r", encoding="utf8") as f:
            return web.Response(text=f.read(), content_type='text/html')
    
    async def static_file(self, request=web.Request):
        """Serve a static file from script root"""
        local_path = os.path.join(self.script_dir, request.rel_url.path[1:])
        print(local_path)
        if os.path.isfile(local_path):
            ext = pathlib.Path(local_path).suffix
            ct = NotificationServer.ext_to_content_type(ext)
            if "text" not in ct:
                with open(local_path, "rb") as f:
                    return web.Response(body=f.read(), content_type=ct)
            else:
                try:
                    with open(local_path, "r", encoding="utf8") as f:
                        return web.Response(text=f.read(), content_type=ct)
                except UnicodeDecodeError as e:
                    self.log.error(f"Unicode Decode error reading file {local_path}")
                    self.log.error(str(e))
                    web.HTTPServerError()
        raise web.HTTPNotFound()
    
    async def notify(self, request=web.Request):
        """REST API Endpoint to send a message to a websocket client"""
        code = request.query.get("code", None)
        event = request.query.get("event", None)
        if code is None or event is None:
            # Code or Msg cannot be
            raise web.HTTPBadRequest(text="400 Bad Request: code or msg is missing")
        event = event.upper().replace(" ", "_")
        found_sid = None
        for sid, registered_code in self.registered_codes.items():
            if registered_code == code:
                found_sid = sid
                break
        data = {}
        for k, v in request.query.items():
            data[k] = v
        if found_sid:
            await self.sio.emit(event, data, sid)
            return web.Response(text="OK", content_type='text/html')
        else:
            raise web.HTTPNotFound(text="404: Provided code not found in list of clients")

    async def on_shutdown(self, app):
        """Handle shutdown signal for aiohttp.web.Application"""
        self.log.info("Shutdown Signal")

    async def on_cleanup(self, app):
        """Handle shutdown signal for aiohttp.web.Application"""
        self.log.info("Cleanup Signal")

    def sig_handler(self, signum, frame):
        signame = signal.Signals(signum).name
        self.log.info(f'Caught Signal {signame} ({signum})')
        print("Caught Signal. Stopping Server...")
        self.stop()
        
    #SocketIO Event Handlers
    async def connect(self, sid, environ, auth):
        """Connect Event Handler"""
        self.log.info(f"Connect Event: {sid}")
        await self.sio.emit("WELCOME", {"message": "Please register your code"})

    async def disconnect(self, sid):
        """Disconnect Event Handler"""
        self.log.info(f"Disconnect Event: {sid}")
        
        code = self.registered_codes.pop(sid, None)
        if code:
            self.log.info(f"Unregistering SID [{sid}]...Success")
        else:
            self.log.info(f"Unregistering SID [{sid}]...Failed. Could not find code.")

    async def register(self, sid, data):
        """
            Client Registers Their Code
            Associate Code with SID
        """
        code = data.get("code", None)
        if code:
            self.log.info(f"Client [{sid}] Registered Code: [{code}]")
            self.registered_codes[sid] = code
            self.log.info(f"Registered Clients: {len(self.registered_codes)}")
        else:
            self.log.info("Code not provided")

    async def event(self, event, sid, data):
        """handles events"""
        self.log.debug(f"Event {event}: {data}")

    def run_app(self, port=8080):
        """Runs the web.Application"""
        self._loop = asyncio.new_event_loop()
        web.run_app(self.app, loop=self._loop, port=port, handle_signals=True)
    
    def stop(self):
        raise web.GracefulExit

    @staticmethod
    def ext_to_content_type(ext, default="text/html"):
        """File Extension to Content-Type Conversion"""
        content_type = default
        if ext == ".js":
            content_type = "text/javascript"
        elif ext == ".css":
            content_type = "text/css"
        elif ext == ".json":
            content_type = "application/json"
        elif ext == ".png":
            content_type = "image/png"
        elif ext == ".jpg":
            content_type = "image/jpeg"
        elif ext == ".gif":
            content_type = "image/gif"
        elif ext == ".ico":
            content_type = "image/vnd.microsoft.icon"
        return content_type

if __name__ == '__main__':
    SCRIPT_DIR = os.path.dirname(__file__)

    parser = argparse.ArgumentParser(
        prog = 'BackBeatBot Notification Server',
        description = 'Small WebSocket/App Server to facilitate websocket notifications',
        epilog = '')

    parser.add_argument("-p", 
        "--port", 
        default=8080,
        type=int,
        help="Specify the listener port number. Default is 8080")
    
    parser.add_argument("-l", 
        "--loglevel", 
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], 
        default="INFO",
        help="Specify the log level. INFO is the default.")

    parser.add_argument("-f", 
        "--logfile", 
        help="Specify log file location. Production location should be <WEBROOT>/log/noti_server.log")

    args = parser.parse_args()
    log_level = logging.getLevelName(args.loglevel)
    if not args.logfile:
        log_file = os.path.join(SCRIPT_DIR, "noti_server.log")

    #Setup Logging
    logging.basicConfig(
        filename=log_file,
        level=log_level,
        filemode="a",
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

    server = NotificationServer(logging)
    port = args.port
    server.run_app(port)