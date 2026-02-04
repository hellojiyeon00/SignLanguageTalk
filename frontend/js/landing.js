// frontend/js/landing.js

document.addEventListener("DOMContentLoaded", () => {
    // 1. 브라우저 금고에서 토큰 확인
    const token = localStorage.getItem("accessToken");
    
    // 2. 버튼들이 들어있는 상자를 가져옴
    const authBox = document.getElementById("authBox");
    
    // 3. 토큰이 있다면? (로그인 상태)
    if (token) {
        // 상자 안의 내용물(로그인, 회원가입 버튼)을 싹 비우고
        // '채팅방 입장' 버튼 하나로 갈아끼웁니다.
        authBox.innerHTML = `
            <a href="chat.html" class="btn-signup">채팅방 바로가기</a>
            <a href="#" onclick="logout()" class="btn-login" style="border:none; color:red;">로그아웃</a>
        `;
    }
});

// (보너스) 로그아웃 기능
function logout() {
    localStorage.removeItem("accessToken");
    localStorage.removeItem("userName");
    alert("로그아웃 되었습니다.");
    window.location.reload(); // 새로고침해서 다시 로그인 버튼 보이게 함
}