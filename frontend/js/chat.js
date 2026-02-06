// frontend/js/chat.js

/**
 * ============================================================================
 * [전역 변수 설정]
 * ============================================================================
 */
const BASE_URL = "http://localhost:8000";
const myId = localStorage.getItem("userId");
const myName = localStorage.getItem("userName"); // 내 이름도 가져옴 (화면 표시용)

let currentRoomId = null; // DB에 저장된 방 번호 (숫자)
let currentRoomName = null; // 소켓 룸 이름 (문자열, 예: "user1_user2")

// 1. 소켓 연결 (서버 주소로 접속)
const socket = io(BASE_URL);

/**
 * ============================================================================
 * [초기화 로직] 페이지 로드 시 실행
 * ============================================================================
 */
document.addEventListener("DOMContentLoaded", () => {
    // 1. 로그인 체크
    if (!myId) {
        alert("로그인이 필요합니다.");
        window.location.href = "login.html";
        return;
    }

    // 2. 내 프로필 이름 표시
    const profileNameEl = document.getElementById("myProfileName");
    if (profileNameEl) {
        profileNameEl.textContent = `${myName}님`;
    }

    // 3. 친구 목록 불러오기
    fetchMyFriends();

    // 4. 엔터키 전송 설정 (채팅 입력창)
    const chatInput = document.getElementById("messageInput");
    if (chatInput) {
        chatInput.addEventListener("keypress", (e) => {
            if (e.key === "Enter") sendMessage();
        });
    }

    // 5. 엔터키 검색 설정 (검색 입력창들)
    const searchInputs = ["searchName", "searchId"];
    searchInputs.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
            el.addEventListener("keypress", (e) => {
                if (e.key === "Enter") searchUser();
            });
        }
    });
});

/**
 * ============================================================================
 * [소켓 이벤트 리스너] 서버에서 메시지가 왔을 때
 * ============================================================================
 */
socket.on("receive_message", (data) => {
    console.log("📥 [Socket] 메시지 수신:", data);
    
    if (data.sender && data.message) {
        // 서버가 준 시간이 없으면 현재 시간 사용
        const timeStr = data.time || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
        displayMessage(data.sender, data.sender_name, data.message, timeStr);
    }
});

/**
 * ============================================================================
 * [API 함수 1] 내 친구 목록 가져오기
 * ============================================================================
 */
async function fetchMyFriends() {
    try {
        const response = await fetch(`${BASE_URL}/chat/list?user_id=${myId}`);
        const friends = await response.json();
        
        const listContainer = document.getElementById("friendList");
        listContainer.innerHTML = ""; // 목록 초기화

        if (!friends || friends.length === 0) {
            listContainer.innerHTML = "<div style='padding:15px; text-align:center; color:#999; font-size:14px;'>등록된 친구가 없습니다.<br>친구를 검색해서 추가해보세요!</div>";
            return;
        }

        friends.forEach(user => {
            //  li 태그 대신 div 태그 사용 (CSS 호환성)
            const itemDiv = document.createElement("div");
            itemDiv.className = "friend-item";
            itemDiv.innerHTML = `
                <div style="font-weight:500;">${user.user_name} <span style="font-size:12px; color:#888;">(${user.user_id})</span></div>
            `;
            // 클릭 시 채팅 시작
            itemDiv.onclick = () => startChat(user, itemDiv);
            
            listContainer.appendChild(itemDiv);
        });

    } catch (error) {
        console.error("❌ 친구 목록 로딩 실패:", error);
    }
}

/**
 * ============================================================================
 * [API 함수 2] 사용자 검색
 * ============================================================================
 */
async function searchUser() {
    const nameVal = document.getElementById("searchName").value.trim();
    const idVal = document.getElementById("searchId").value.trim();

    if (!nameVal && !idVal) {
        alert("이름 또는 아이디를 입력해주세요.");
        return;
    }

    try {
        // 쿼리 파라미터 생성
        let queryParams = `my_id=${myId}`;
        if (nameVal) queryParams += `&name=${encodeURIComponent(nameVal)}`;
        if (idVal) queryParams += `&member_id=${encodeURIComponent(idVal)}`;

        const response = await fetch(`${BASE_URL}/chat/search?${queryParams}`);
        const results = await response.json();

        // UI 표시
        const resultArea = document.getElementById("searchResultArea");
        const resultList = document.getElementById("searchResultList");
        resultArea.style.display = "block";
        resultList.innerHTML = "";

        if (results.length === 0) {
            resultList.innerHTML = "<div style='padding:10px; color:#777; font-size:13px;'>검색 결과가 없습니다.</div>";
            return;
        }

        results.forEach(user => {
            const itemDiv = document.createElement("div");
            itemDiv.className = "friend-item"; // 스타일 재사용
            itemDiv.style.marginBottom = "5px";
            itemDiv.style.cursor = "default"; // 검색 결과는 클릭해서 채팅하는게 아님 (버튼 눌러야 함)
            
            itemDiv.innerHTML = `
                <div>
                    <span style="font-weight:bold;">${user.user_name}</span>
                    <span style="font-size:12px; color:#666;">(${user.member_id})</span>
                </div>
            `;

            // '대화하기(추가)' 버튼 생성
            const addBtn = document.createElement("button");
            addBtn.textContent = "추가";
            addBtn.style.cssText = "font-size:12px; padding:4px 8px; cursor:pointer; background:#007bff; color:white; border:none; border-radius:4px;";
            addBtn.onclick = (e) => {
                e.stopPropagation(); // 부모 클릭 이벤트 전파 방지
                addFriend(user.member_id);
            };

            itemDiv.appendChild(addBtn);
            resultList.appendChild(itemDiv);
        });

    } catch (error) {
        console.error("❌ 검색 실패:", error);
        alert("검색 중 오류가 발생했습니다.");
    }
}

// [UI] 검색창 닫기
function closeSearch() {
    document.getElementById("searchResultArea").style.display = "none";
    document.getElementById("searchName").value = "";
    document.getElementById("searchId").value = "";
}

/**
 * ============================================================================
 * [API 함수 3] 친구 추가
 * ============================================================================
 */
async function addFriend(targetId) {
    if(!confirm(`'${targetId}'님을 친구로 추가하시겠습니까?`)) return;

    try {
        const response = await fetch(`${BASE_URL}/chat/room`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ my_id: myId, target_id: targetId })
        });

        const result = await response.json();
        alert(result.message);

        // UI 업데이트: 검색창 닫고 목록 새로고침
        closeSearch();
        fetchMyFriends(); 

    } catch (error) {
        console.error("❌ 친구 추가 실패:", error);
    }
}

/**
 * ============================================================================
 * [채팅 핵심 로직] 채팅방 입장 (startChat)
 * ============================================================================
 */
async function startChat(friend, clickedElement) {
    // 1. UI 활성화 처리 (선택된 친구 색깔 바꾸기)
    const allItems = document.querySelectorAll('.friend-item');
    allItems.forEach(item => item.classList.remove('active'));
    if (clickedElement) clickedElement.classList.add('active');

    // 2. 이전 방이 있다면 퇴장 처리
    if (currentRoomName) {
        socket.emit("leave_room", { room: currentRoomName, username: myId });
    }

    try {
        // 3. 서버에서 방 번호(room_id) 조회 (없으면 생성됨)
        const roomRes = await fetch(`${BASE_URL}/chat/room`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ my_id: myId, target_id: friend.user_id })
        });
        const roomData = await roomRes.json();
        currentRoomId = roomData.room_id; // DB ID 저장

        // 4. 소켓 룸 이름 생성 (문자열) 및 전역 변수 갱신
        // 예: user1_user2 (알파벳 순서로 정렬하여 항상 같은 이름이 되도록 함)
        const participants = [myId, friend.user_id].sort(); 
        currentRoomName = participants.join("_");

        // 5. 화면 초기화 및 제목 설정
        document.getElementById("messages").innerHTML = "";
        document.getElementById("chatTitle").textContent = `${friend.user_name}님과의 대화`;
        document.getElementById("messageInput").focus();

        // 6. 소켓 방 입장 (서버에 알림)
        socket.emit("join_room", { room: currentRoomName, username: myId });
        console.log(`🏠 [Socket] 방 입장: ${currentRoomName} (ID: ${currentRoomId})`);

        // 7. 과거 대화 내역 불러오기 (History)
        const historyRes = await fetch(`${BASE_URL}/chat/history/${currentRoomId}`);
        const historyArr = await historyRes.json();

        // 과거 메시지 화면에 그리기
        historyArr.forEach(chat => {
            // 시간 포맷팅 (YYYY-MM-DDTHH:mm:ss -> HH:mm)
            let timeStr = chat.date; 
            try {
                const dateObj = new Date(chat.date);
                if (!isNaN(dateObj)) {
                    timeStr = dateObj.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
                }
            } catch(e) {} // 파싱 실패 시 원본 문자열 사용

            displayMessage(chat.sender, chat.sender_name, chat.message, timeStr); 
        });

        // 스크롤 맨 아래로
        const msgBox = document.getElementById("messages");
        msgBox.scrollTop = msgBox.scrollHeight;

    } catch (error) {
        console.error("❌ 채팅방 입장 실패:", error);
        alert("채팅방을 불러오는 데 실패했습니다.");
    }
}

/**
 * ============================================================================
 * [채팅 핵심 로직] 메시지 전송 (sendMessage)
 * ============================================================================
 */
function sendMessage() {
    const input = document.getElementById("messageInput");
    const msg = input.value.trim(); // 공백 제거

    if (!msg) return; // 빈 메시지는 안 보냄
    if (!currentRoomName || !currentRoomId) {
        alert("대화 상대를 먼저 선택해주세요.");
        return;
    }

    // 소켓으로 메시지 전송
    socket.emit("send_message", {
        room: currentRoomName,      // 소켓 방 이름
        room_id: currentRoomId,     // DB 방 번호
        username: myId,             // 보낸 사람 ID
        message: msg                // 메시지 내용
    });

    console.log(`📤 [Socket] 전송: ${msg}`);
    input.value = ""; // 입력창 비우기
    input.focus();    // 다시 입력할 수 있게 포커스
}

/**
 * ============================================================================
 * [UI 함수] 화면에 말풍선 그리기 (displayMessage)
 * ============================================================================
 */
function displayMessage(senderId, senderName, msg, time) {
    const msgBox = document.getElementById("messages");
    const isMine = (senderId === myId); // 내가 보낸 메시지인지 확인

    // 1. 메시지 전체 틀 (Row)
    const rowDiv = document.createElement("div");
    rowDiv.className = `message-row ${isMine ? "message-mine" : "message-other"}`;

    // 2. 이름표 (상대방일 때만 표시, CSS에서 내 이름은 숨김 처리됨)
    const nameDiv = document.createElement("div");
    nameDiv.className = "message-name";
    nameDiv.textContent = senderName;

    // 3. 내용 컨테이너 (말풍선 + 시간)
    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content"; // CSS 리팩토링된 클래스 사용!

    // 말풍선
    const bubbleDiv = document.createElement("div");
    bubbleDiv.className = "message-bubble";
    bubbleDiv.textContent = msg;

    // 시간
    const timeSpan = document.createElement("span");
    timeSpan.className = "message-time";
    timeSpan.textContent = time;

    // 4. 조립 (순서는 CSS flex-direction으로 제어하므로 단순 append)
    contentDiv.appendChild(bubbleDiv);
    contentDiv.appendChild(timeSpan);
    
    rowDiv.appendChild(nameDiv);
    rowDiv.appendChild(contentDiv);

    msgBox.appendChild(rowDiv);
    
    // 5. 스크롤을 맨 아래로 이동 (새 메시지 보이게)
    msgBox.scrollTop = msgBox.scrollHeight;
}

/**
 * ============================================================================
 * [기타] 로그아웃
 * ============================================================================
 */
function logout() {
    if(confirm("로그아웃 하시겠습니까?")) {
        localStorage.clear();
        window.location.href = "index.html";
    }
}