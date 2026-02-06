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
        if (authBox) {
            authBox.innerHTML = `
                <a href="chat.html" class="btn-signup">채팅방 입장</a>
                <button id="headerLogoutBtn" class="btn-logout">로그아웃</button>
            `;
            
            // 동적으로 생성된 로그아웃 버튼에 이벤트 연결
            document.getElementById("headerLogoutBtn").addEventListener("click", handleLogout);
        }

        // 3-2. 중앙 히어로 버튼 변경
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
    // [수정 2] 묻지도 따지지도 않고 즉시 로그아웃 (confirm 삭제)
    
    // 1. 저장된 모든 정보 삭제
    localStorage.clear();
    
    // 2. 페이지 새로고침 (로그인 전 상태로 복구)
    // alert("로그아웃 되었습니다."); // 알림도 굳이 필요 없다면 주석 처리하거나 삭제하세요.
    window.location.reload();
}