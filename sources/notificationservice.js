var debug = false;
const queryParams = new URLSearchParams(window.location.search);
const code = queryParams.get("code");

if(code===null){
    console.log("No Code Provided. Alert will not work.")
}else{
    
}
var socket = io();

// Log events to console for debugging
socket.onAny((event, ...args) => {
    if(debug){
        console.log(`got ${event}`);
    }
});

socket.on('WELCOME', function(data) {
    if(code===null){ return }
    // Respond with a message including this clients' code
    socket.emit("REGISTER", {"code": code});
});

socket.on('DEBUG', function(data) {
    console.log("DEBUG EVENT:")
    console.log(data)
});

socket.on('error', console.error.bind(console));
socket.on('message', console.log.bind(console));