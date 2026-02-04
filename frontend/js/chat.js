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
    fetchMyFriends();

    // 엔터키 전송 기능
    const input = document.getElementById("messageInput");
    input.addEventListener("keypress", (e) => {
        // 눌린 키가 'Enter'라면?
        if (e.key === "Enter") {
            sendMessage(); // 전송 버튼 누른 것과 똑같이 동작해라!
        }
    });
});

// 1. [수정됨] 내 친구 목록 가져오기
async function fetchMyFriends() {
    try {
        // API 주소가 /auth/users 에서 /auth/friends 로 바뀌었습니다!
        // 내 ID를 쿼리 파라미터(?user_id=...)로 같이 보냅니다.
        const response = await fetch(`${BASE_URL}/auth/friends?user_id=${myId}`);
        const friends = await response.json();
        
        const listContainer = document.getElementById("friendList");
        listContainer.innerHTML = "";

        if (friends.length === 0) {
            listContainer.innerHTML = "<li style='padding:10px; color:#999;'>등록된 친구가 없습니다.<br>친구를 검색해서 추가해보세요!</li>";
            return;
        }

        friends.forEach(user => {
            const li = document.createElement("li");
            li.className = "friend-item";
            li.textContent = user.user_name; // 친구 이름
            li.onclick = () => startChat(user);
            listContainer.appendChild(li);
        });

    } catch (error) {
        console.error("친구 목록 로딩 실패", error);
    }
}

// 2. [신규] 친구 검색 기능
async function searchUser() {
    const keyword = document.getElementById("searchInput").value;
    if (!keyword) {
        alert("검색어를 입력하세요");
        return;
    }

    try {
        // 검색 API 호출
        const response = await fetch(`${BASE_URL}/auth/search?keyword=${keyword}&user_id=${myId}`);
        const results = await response.json();

        // 검색 결과창 보여주기
        const resultArea = document.getElementById("searchResultArea");
        const resultList = document.getElementById("searchResultList");
        resultArea.style.display = "block"; // 숨겨둔 창 열기
        resultList.innerHTML = ""; // 기존 결과 초기화

        if (results.length === 0) {
            resultList.innerHTML = "<li>검색 결과가 없습니다.</li>";
            return;
        }

        results.forEach(user => {
            const li = document.createElement("li");
            li.style.padding = "5px";
            li.style.borderBottom = "1px solid #ccc";
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            
            // 이름과 '추가' 버튼 만들기
            li.innerHTML = `
                <span>${user.user_name} (${user.user_id})</span>
                <button onclick="addFriend('${user.user_id}')" style="font-size:12px;">추가</button>
            `;
            resultList.appendChild(li);
        });

    } catch (error) {
        console.error("검색 실패", error);
    }
}

// 3. [신규] 친구 추가 기능
async function addFriend(friendId) {
    if(!confirm("이 사용자를 친구로 추가하시겠습니까?")) return;

    try {
        const response = await fetch(`${BASE_URL}/auth/friends`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: myId,
                friend_id: friendId
            })
        });

        const result = await response.json();
        alert(result.message);

        // 추가가 끝났으니 검색창 닫고, 친구 목록 새로고침!
        closeSearch();
        fetchMyFriends(); 

    } catch (error) {
        console.error("친구 추가 실패", error);
    }
}

// 검색창 닫기
function closeSearch() {
    document.getElementById("searchResultArea").style.display = "none";
    document.getElementById("searchInput").value = "";
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