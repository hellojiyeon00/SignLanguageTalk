// frontend/js/landing.js

document.addEventListener("DOMContentLoaded", () => {
    // 1. 브라우저 저장소(Local Storage)에서 토큰 확인
    const token = localStorage.getItem("accessToken");
    
    // 2. 조작할 요소들 가져오기
    const authBox = document.getElementById("authBox");   // 상단 헤더 버튼 그룹
    const startBtn = document.getElementById("startBtn"); // 중앙 '지금 시작하기' 버튼

    // 3. 토큰이 있다면? (이미 로그인 된 상태)
    if (token) {
        // 3-1. 상단 헤더 버튼 변경
        // '로그인/회원가입' -> '채팅방 입장/로그아웃'
        if (authBox) {
            authBox.innerHTML = `
                <a href="chat.html" class="btn-signup">채팅방 입장</a>
                <button id="headerLogoutBtn" class="btn-login" style="cursor:pointer;">로그아웃</button>
            `;
            
            // 동적으로 생성된 로그아웃 버튼에 이벤트 연결
            document.getElementById("headerLogoutBtn").addEventListener("click", handleLogout);
        }

        // 3-2. 중앙 히어로 버튼 변경
        // '지금 시작하기' -> '채팅방 입장하기'
        if (startBtn) {
            startBtn.href = "chat.html";
            startBtn.textContent = "채팅방 입장하기";
        }
    }
});

/**
 * ============================================================================
 * [로그아웃 로직]
 * ============================================================================
 */
function handleLogout() {
    if (confirm("로그아웃 하시겠습니까?")) {
        // 1. 저장된 모든 정보 삭제 (토큰, 아이디, 이름 등)
        localStorage.clear();
        
        // 2. 사용자에게 알림
        alert("로그아웃 되었습니다.");
        
        // 3. 페이지 새로고침 (로그인 전 상태로 복구)
        window.location.reload();
    }
}