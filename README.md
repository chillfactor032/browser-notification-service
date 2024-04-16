# Browser Notification Service

This is a Python, socket.io, aiohttp server that uses websockets to deliver notifications to html clients. This service is meant to trigger events in browser source-based OBS style alerts, but could have other applications as well.

## Serving Files Over HTTP

Files stored in `<WEB_ROOT>/sources` will get served. Additional routes could be added to `notification_server.py` if needed. If a file isn't served correctly make sure the correct MIME type is being sent. There is a table in `NotificationServer.ext_to_content_type(ext)` that converts file extensions to MIME Types to be sent in Content-Type header.

## Setup

```bash
git clone https://github.com/chillfactor032/browser-notification-service.git
cd browser-notification-service
py -m pip install -r requirements.txt
```

## Usage

```bash
py notification_server.py -h
usage: BackBeatBot Notification Server [-h] [-p PORT] [-l {DEBUG,INFO,WARNING,ERROR,CRITICAL}] [-f LOGFILE]

Small WebSocket/App Server to facilitate websocket notifications

options:
  -h, --help            show this help message and exit
  -p PORT, --port PORT  Specify the listener port number. Default is 8080
  -l {DEBUG,INFO,WARNING,ERROR,CRITICAL}, --loglevel {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Specify the log level. INFO is the default.
  -f LOGFILE, --logfile LOGFILE
                        Specify log file location. Production location should be <WEBROOT>/log/noti_server.log
```

## Registering For Events

Web pages can register themselves for events by connecting to the websocket and providing a code as a query parameter. The websocket server will register this code and know to forward events to the connection using that code.

### Example

Create an html page and connect to the websocket. Do this by adding the file to the `./sources/` directory and including the provided `notificationservice.js` file included with this repo. 

```html
<!DOCTYPE html>
<html>
<head>
    <script src="https://cdn.socket.io/4.7.5/socket.io.js"></script>
    <script src="notificationservice.js"></script>
<script>
//Register Callbacks for events you are intersted in
socket.on('DEBUG', function(data) {
    console.log("DEBUG EVENT:")
    console.log(data)
});
</script>
</head>
<body>
    When a websocket event is recieved, it will be output to the javascript console.
</body>
</html>
```

When the page is loaded be sure to register with the service by adding a code in the url like:

`http://mysite.com:8080/sources/alert.html?code=1234`

Now you can forward any event to this page by making the API call:

`http://mysite.com:8080/sources/alert.html?code=1234&event=EVENTNAME&foo=bar`

Notice all query parameters are included in the event, including event name and code.

## Running systemctl Service

The Browser Notification Service can be run as a systemctl service. Create the file `/etc/systemd/system/notiservice.service'

```ini
[Unit]
Description=Control browser-notification-service
After=multi-user.target

[Service]
ExecStart=python3 <CLONE_DIR>/browser-notification-service/notification_server.py -H <HOST> -p <PORT> -f <LOGFILE_PATH>
Type=simple
Restart=always

[Install]
WantedBy=multi-user.target
```

Save this file. The service can now be stopped, started, and restarted as a systemctl service.

```bash
systemctl start notiservice.service
systemctl stop notiservice.service
systemctl restart notiservice.service
```

## Enable SSL

If SSL is required, create an ssl context json file that contains paths to the certificate and key files. These files construct a python ssl_context passed to aiohttp. The file format is as follows:

```json
{
    "cert": "<path to cert>",
    "key": "<path to cert key>"
}
```

To use the SSL context, call the server script with the argument `--sslcontext <PATH TO SSL FILE>`.

## Troubleshooting

If changes are made to the service and the systemctl service won't start, try `sudo /bin/systemctl daemon-reload`
