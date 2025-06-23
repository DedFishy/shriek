const nameInput = document.getElementById("name-input");
const namePopup = document.getElementById("name-popup");
const messageDisplay = document.getElementById("message-display");
const messageInput = document.getElementById("message-input")
const messageList = document.getElementById("message-list");
const userList = document.getElementById("user-list")

var socket = io();

function isSuccess(data) {return data["type"] == "success";}

function doIfEnter(event, func) {
    if (event.keyCode == 13) func();
}

function until(conditionFunction) {

  const poll = resolve => {
    if(conditionFunction()) resolve();
    else setTimeout(_ => poll(resolve), 400);
  }

  return new Promise(poll);
}

function showMessage(message, timeout=5000) {
    messageDisplay.classList.add("visible");
    messageDisplay.innerText = message;
    setTimeout(() => {messageDisplay.classList.remove("visible")}, timeout)
}

function addMessage(senderName, content) {
    var messageElement = document.createElement("div");
    messageElement.className = "message";
    
    senderElement = document.createElement("div");
    senderElement.className = "message-sender";
    senderElement.innerText = senderName;
    messageElement.appendChild(senderElement);

    contentElement = document.createElement("div")
    contentElement.className = "message-content";
    contentElement.innerText = content;
    messageElement.appendChild(contentElement);

    messageList.appendChild(messageElement);

    messageElement.scrollIntoView();
}

function processRoomUpdate(data) {
    userList.innerHTML = "";
    data["userlist"].forEach((user) => {
        var userElement = document.createElement("div");
        userElement.className = "user-list-item";
        userElement.innerText = user["name"];
        if (user["call_participant_id"] != -1) {
            var inCallEmoji = document.createElement("div");
            inCallEmoji.className = "in-call-emoji";
            inCallEmoji.innerText = "☎️";
            userElement.appendChild(inCallEmoji);
        }
        userList.appendChild(userElement);
    })
}

async function emitAndWait(message, data, waitingFor, timeout) {
    var returned = undefined;
    socket.on(waitingFor, (data) => {
        returned = data;
        if (returned == undefined) {
            socket.off(waitingFor);
            returned = {}
        };
        
    })
    socket.emit(message, data);
    startTime = Date.now();
    await until(_ => (returned != undefined) | (Date.now() - startTime > timeout));
    socket.off(waitingFor);
    return returned;
}

async function submitName() {
    console.log("Submitting name...")
    var name = nameInput.value;
    serverResponse = await emitAndWait("tryJoin", {"name": name}, "tryJoinResponse", 5000);
    console.log(serverResponse);
    if (isSuccess(serverResponse)) {
        launchChat();
    } else {
        showMessage(serverResponse["message"]);
    }
}

socket.on("roomUpdate", (data) => {
    console.log("ROOM UPDATE");
    console.log(data);
    processRoomUpdate(data);
})

socket.on("userMessage", (data) => {
    console.log(data);
    addMessage(data["sender"]["name"], data["content"])
})

function launchChat() {
    namePopup.classList.remove("visible");
}

function sendMessage() {
    message = messageInput.value;
    if (message != "") {
        socket.emit("sendMessage", {"content": message});
    }
    messageInput.value = "";
}

let micTrack;
let micRecorder;
let transferInProgress = false;
function joinCall() {
    navigator.mediaDevices.getUserMedia({audio: true, video: false})
    .then((stream) => {

        socket.emit("joinVoice");
        
        micRecorder = new MediaRecorder(stream, {"mimeType": "audio/webm"});
        micRecorder.ondataavailable = event => {
            console.log("Transferring frame")
            if (transferInProgress) return;
            transferInProgress = true;
            const blob = event.data;
            socket.emit("voiceFrame", blob);
            transferInProgress = false;
        }
        micRecorder.start(100);
    

    })
}

let globufs = []

function createVoiceChannel(id) {

    console.log("Creating voice channel: " + id);
    let audio = document.createElement("audio")
    let player = new MediaSource()
    audio.src = URL.createObjectURL(player);
    console.log(player.readyState);
    
    let buffer = undefined;

    socket.on("userVoiceFrame-" + id, (data) => {
        if (buffer == undefined) {
            buffer = player.addSourceBuffer('video/webm; codecs="vp8,opus"')
        }
        console.log("Updating " + id)
        buffer.appendBuffer(data)
        
        if (audio.paused) audio.play();
    })
}

socket.on("constructVoiceChannel", (data) => {
    createVoiceChannel(data["participant_id"])
})

socket.on("destroyVoiceChannel", (data) => {
    id = data["participant_id"];
    socket.off("userVoiceFrame-" + id);
})