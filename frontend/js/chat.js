// frontend/js/chat.js

let currentRoomId = null;
const BASE_URL = "http://localhost:8000";
const myId = localStorage.getItem("userId");

// 1. 소켓 연결 및 리스너 등록 (가장 먼저 수행!)
const socket = io(BASE_URL);
let currentRoom = null;

// [해결책] 서버에서 온 메시지를 처리하는 핵심 로직
socket.on("receive_message", (data) => {
    console.log("📥 서버에서 받은 데이터:", data); // F12 콘솔에서 확인 가능
    
    if (data.sender && data.message) {
        // 서버가 준 시간이 없으면 내 컴퓨터 현재 시간을 씁니다.
        const time = data.time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        displayMessage(data.sender, data.sender_name, data.message, time);
    }
});

// 페이지 로딩 시 초기화
document.addEventListener("DOMContentLoaded", () => {
    if (!myId) {
        alert("로그인 정보가 없습니다.");
        window.location.href = "login.html";
        return;
    }
    const myName = localStorage.getItem("userName");
    document.getElementById("myProfileName").textContent = myName + "님";
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
        // 주소가 /auth/friends -> /chat/list 로 바뀌었습니다.
        // 내 ID를 쿼리 파라미터(?user_id=...)로 같이 보냅니다.
        const response = await fetch(`${BASE_URL}/chat/list?user_id=${myId}`);
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
            li.textContent = `${user.user_name} (${user.user_id})`; // 친구 이름
            li.onclick = () => startChat(user);
            listContainer.appendChild(li);
        });

    } catch (error) {
        console.error("친구 목록 로딩 실패", error);
    }
}

// 2. [신규] 친구 검색 기능
async function searchUser() {
    // 1. 두 입력창의 값을 가져옵니다.
    const nameVal = document.getElementById("searchName").value.trim();
    const idVal = document.getElementById("searchId").value.trim();

    // 2. 둘 다 비어있으면 경고
    if (!nameVal && !idVal) {
        alert("이름 또는 아이디를 입력해주세요.");
        return;
    }

    try {
        // 3. 쿼리 파라미터 조립 (?name=...&member_id=...)
        // 값이 있는 것만 보냅니다.
        let queryParams = `my_id=${myId}`;
        if (nameVal) queryParams += `&name=${encodeURIComponent(nameVal)}`;
        if (idVal) queryParams += `&member_id=${encodeURIComponent(idVal)}`;

        // 4. API 호출
        const response = await fetch(`${BASE_URL}/chat/search?${queryParams}`);
        const results = await response.json();

        // 5. 결과 표시 (기존 로직과 동일)
        const resultArea = document.getElementById("searchResultArea");
        const resultList = document.getElementById("searchResultList");
        resultArea.style.display = "block";
        resultList.innerHTML = "";

        if (results.length === 0) {
            resultList.innerHTML = "<li style='padding:5px; color:#777;'>검색 결과가 없습니다.</li>";
            return;
        }

        results.forEach(user => {
            const li = document.createElement("li");
            li.style.padding = "8px 5px";
            li.style.borderBottom = "1px solid #eee";
            li.style.display = "flex";
            li.style.justifyContent = "space-between";
            li.style.alignItems = "center";
        
            li.innerHTML = `
                <div>
                    <span style="font-weight:bold;">${user.user_name}</span>
                    <span style="font-size:12px; color:#666;">(${user.member_id})</span>
                </div>
                <button onclick="addFriend('${user.member_id}')" 
                    style="font-size:12px; padding:3px 8px; cursor:pointer;">
                    대화
                </button>
            `;
            resultList.appendChild(li);
        });

    } catch (error) {
        console.error("검색 실패", error);
        alert("검색 중 오류가 발생했습니다.");
    }
}

// [수정] 검색창 닫기 (입력값도 초기화)
function closeSearch() {
    document.getElementById("searchResultArea").style.display = "none";
    document.getElementById("searchName").value = "";
    document.getElementById("searchId").value = "";
}

// 3. [신규] 친구 추가 기능
async function addFriend(targetId) {
    if(!confirm("이 사용자와 대화를 시작하시겠습니까?")) return;

    try {
        const response = await fetch(`${BASE_URL}/chat/room`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                my_id: myId,
                target_id: targetId
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

// 4. 채팅 시작 함수 (친구 클릭 시)
async function startChat(friend) {
    // 1. 이전 방 퇴장 (기존 로직 유지)
    if (currentRoom) {
        socket.emit("leave_room", { room: currentRoom, username: myId });
    }

    try {
        // 2. [신규] 서버에서 방 번호(talk_room_id)를 먼저 알아옵니다.
        const roomRes = await fetch(`${BASE_URL}/chat/room`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ my_id: myId, target_id: friend.user_id })
        });
        const roomData = await roomRes.json();
        currentRoomId = roomData.room_id; // DB 저장을 위해 숫자로 된 ID를 전역 변수에 저장

        // 3. [신규] 해당 방의 과거 대화 내역(history)을 서버에 요청합니다.
        const historyRes = await fetch(`${BASE_URL}/chat/history/${currentRoomId}`);
        const historyArr = await historyRes.json();

        // 4. 화면 초기화 (메시지 창 비우기)
        document.getElementById("messages").innerHTML = "";

        // 5. [신규] 받아온 과거 내역을 화면에 하나씩 그려줍니다.
        historyArr.forEach(chat => {
    displayMessage(chat.sender, chat.sender_name, chat.message, chat.date); 
        });

        // 6. [기존 유지] 새로운 방 이름 생성 (ID 기반)
        const participants = [myId, friend.user_id].sort(); 
        const roomName = participants.join("_");
        currentRoom = roomName;

        // 7. [기존 유지] 친구 목록 버튼 스타일 변경 (Active 클래스)
        const allItems = document.querySelectorAll('.friend-item');
        allItems.forEach(item => item.classList.remove('active'));

        const targetText = `${friend.user_name} (${friend.user_id})`; // 목록에 표시된 텍스트와 비교
        allItems.forEach(item => {
            if (item.textContent === targetText) {
                item.classList.add('active'); // 클릭한 친구만 강조
            }
        });

        // 8. [기존 유지] 채팅창 제목 변경 및 소켓 입장
        console.log(`🏠 입장: ${roomName}`);
        document.getElementById("chatTitle").textContent = `${friend.user_name}님과의 대화`;
        socket.emit("join_room", { room: roomName, username: myId });

    } catch (error) {
        console.error("방 정보를 가져오거나 대화 내역을 불러오는 데 실패했습니다.", error);
        alert("대화 내역을 불러올 수 없습니다.");
    }
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
        room_id: currentRoomId, // [추가] DB 저장을 위해 필수!
        username: myId,
        message: msg
    });

    input.value = "";
}

function displayMessage(senderId, senderName, msg, time) {
    const msgBox = document.getElementById("messages");
    
    const rowDiv = document.createElement("div");
    rowDiv.className = `message-row ${senderId === myId ? "message-mine" : "message-other"}`;

    // [중요] '내 메시지인지' 판별할 때는 고유한 ID(senderId)를 사용합니다.
    rowDiv.className = `message-row ${senderId === myId ? "message-mine" : "message-other"}`;

    // 이름표
    const nameDiv = document.createElement("div");
    nameDiv.className = "message-name";
    nameDiv.textContent = senderName;

    // 말풍선과 시간을 가로로 나란히 놓기 위한 박스
    const contentDiv = document.createElement("div");
    contentDiv.style.display = "flex";
    contentDiv.style.alignItems = "flex-end"; // 둘 다 바닥에 맞춤

    // 말풍선
    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "message-bubble";
    bubbleDiv.textContent = msg;

    // [시간 추가]
    const timeSpan = document.createElement("span");
    timeSpan.className = "message-time";
    timeSpan.textContent = time; // "14:30" 글자를 넣음

    // 조립: 내용 박스 안에 말풍선과 시간을 넣습니다.
    contentDiv.appendChild(bubbleDiv);
    contentDiv.appendChild(timeSpan);
    
    rowDiv.appendChild(nameDiv);
    rowDiv.appendChild(contentDiv); // 최종 조립

    msgBox.appendChild(rowDiv);
    msgBox.scrollTop = msgBox.scrollHeight; // 새 메시지가 오면 맨 아래로 스크롤
}

// 6. 로그아웃
function logout() {
    localStorage.clear();
    window.location.href = "index.html";
}