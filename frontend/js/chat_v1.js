// frontend/js/chat.js

const BASE_URL = "http://localhost:8000";
const myId = localStorage.getItem("userName"); 

// 1. 소켓 연결 및 리스너 등록 (가장 먼저 수행!)
const socket = io(BASE_URL);
let currentRoom = null;

// [해결책] 서버에서 온 메시지를 처리하는 핵심 로직
socket.on("receive_message", (data) => {
    console.log("📥 서버에서 받은 데이터:", data); // F12 콘솔에서 확인 가능
    
    // 데이터의 이름표가 'sender'와 'message'인지 확인
    if (data.sender && data.message) {
        displayMessage(data.sender, data.message);
    }
});

// 페이지 로딩 시 초기화
document.addEventListener("DOMContentLoaded", () => {
    if (!myId) {
        alert("로그인 정보가 없습니다.");
        window.location.href = "login.html";
        return;
    }
    document.getElementById("myProfileName").textContent = myId + "님";
    fetchUserList();

    // 엔터키 전송 기능
    const input = document.getElementById("messageInput");
    input.addEventListener("keypress", (e) => {
        // 눌린 키가 'Enter'라면?
        if (e.key === "Enter") {
            sendMessage(); // 전송 버튼 누른 것과 똑같이 동작해라!
        }
    });
});

// 친구 목록 가져오기 (기존 동일)
async function fetchUserList() {
    try {
        const response = await fetch(`${BASE_URL}/auth/users`);
        const users = await response.json();
        const listContainer = document.getElementById("friendList");
        listContainer.innerHTML = "";

        users.forEach(user => {
            if (user.user_name === myId) return; 
            const li = document.createElement("li");
            li.className = "friend-item";
            li.textContent = user.user_name;
            li.onclick = () => startChat(user);
            listContainer.appendChild(li);
        });
    } catch (error) {
        console.error("❌ 유저 목록 호출 실패:", error);
    }
}

// 채팅 시작 (방 입장)
function startChat(friend) {
    const participants = [myId, friend.user_name].sort(); 
    const roomName = participants.join("_");
    currentRoom = roomName;

    console.log(`🏠 방 입장: ${roomName}`);
    document.getElementById("chatTitle").textContent = `${friend.user_name}님과의 대화`;
    document.getElementById("messages").innerHTML = ""; 

    socket.emit("join_room", { room: roomName, username: myId });
}

// 메시지 전송 (버튼 클릭 시)
function sendMessage() {
    const input = document.getElementById("messageInput");
    const msg = input.value;

    if (!msg) return;
    if (!currentRoom) {
        alert("대화 상대를 먼저 선택해주세요.");
        return;
    }

    console.log(`📤 메시지 전송: ${msg}`);
    
    // 서버와 약속한 Key 이름(username, message)을 정확히 사용
    socket.emit("send_message", {
        room: currentRoom,
        username: myId,
        message: msg
    });

    input.value = "";
}

// [수정됨] 화면에 메시지 그리기 (카카오톡 스타일)
function displayMessage(sender, msg) {
    const msgBox = document.getElementById("messages");
    
    // 1. 메시지 전체를 감싸는 틀 생성
    const rowDiv = document.createElement("div");
    rowDiv.className = "message-row";

    // 2. 내가 보낸 건지 확인 (중요!)
    if (sender === myId) {
        rowDiv.classList.add("message-mine"); // 오른쪽 배치 클래스 추가
    } else {
        rowDiv.classList.add("message-other"); // 왼쪽 배치 클래스 추가
    }

    // 3. 이름표 만들기
    // (내가 보낸 메시지는 CSS에서 display: none으로 숨겨집니다)
    const nameDiv = document.createElement("div");
    nameDiv.className = "message-name";
    nameDiv.textContent = sender;

    // 4. 말풍선 만들기
    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "message-bubble";
    bubbleDiv.textContent = msg;

    // 5. 조립하기 (틀 안에 이름과 말풍선을 넣음)
    rowDiv.appendChild(nameDiv);
    rowDiv.appendChild(bubbleDiv);

    // 6. 화면에 추가
    msgBox.appendChild(rowDiv);
    
    // 7. 스크롤 맨 아래로 내리기
    msgBox.scrollTop = msgBox.scrollHeight;
}

// 6. 로그아웃
function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}