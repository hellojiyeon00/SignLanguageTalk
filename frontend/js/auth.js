// frontend/js/auth.js

// [설정] 백엔드 서버 주소 (팀장님의 uvicorn 주소)
const BASE_URL = "http://localhost:8000";

// 유효성 검사
const validators = {
    // 아이디: 영문/숫자 4자 이상
    id: (val) => /^[a-zA-Z0-9]{4,}$/.test(val),
    // 비밀번호: 8자 이상
    pw: (val) => val.length >= 8,
    // 이름: 한글 2자 이상
    name: (val) => /^[가-힣]{2,}$/.test(val),
    // 전화번호: 010-0000-0000 형식
    phone: (val) => /^010-\d{4}-\d{4}$/.test(val),
    // 이메일: 이메일 형식
    email: (val) => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)
};

function toggleError(inputId, errorId, isValid) {
    const input = document.getElementById(inputId);
    const errorMsg = document.getElementById(errorId);
    
    // 해당 요소가 없으면(예: 로그인 페이지라 회원가입 창이 없을 때) 무시
    if (!input || !errorMsg) return isValid; 

    if (isValid) {
        input.classList.remove("input-error");
        errorMsg.classList.remove("show");
    } else {
        input.classList.add("input-error");
        errorMsg.classList.add("show");
    }
    return isValid;
}

// 1. 로그인 처리 함수
async function handleLogin() {
    const userId = document.getElementById("loginId").value;
    const userPw = document.getElementById("loginPw").value;

    if (!userId || !userPw) {
        alert("아이디와 비밀번호를 모두 입력해주세요.");
        return;
    }

    try {
        // 백엔드(/auth/login)에 POST 요청 보내기
        const response = await fetch(`${BASE_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                user_id: userId,
                password: userPw
            })
        });

        const data = await response.json();

        if (response.ok) {
            // 성공 시: 받은 JWT(입장권)를 브라우저 저장소(localStorage)에 보관
            localStorage.setItem("accessToken", data.access_token);
            localStorage.setItem("userName", data.user_name);
            alert(data.message); // "로그인 성공!"
            
            // 메인 페이지(채팅방)로 이동 (추후 구현)
            window.location.href = "index.html"; 
        } else {
            // 실패 시: 백엔드가 보낸 에러 메시지 출력
            alert(`로그인 실패: ${data.detail}`);
        }
    } catch (error) {
        console.error("Login Error:", error);
        alert("서버와 통신 중 오류가 발생했습니다.");
    }
}

// 3. 회원가입 처리 함수 (수정됨)
async function handleSignup() {
    // 값을 먼저 다 가져옵니다.
    const id = document.getElementById("signupId").value;
    const pw = document.getElementById("signupPw").value;
    const name = document.getElementById("signupName").value;
    const phone = document.getElementById("signupPhone").value;
    const email = document.getElementById("signupEmail").value;

    // ============================================================
    // [2. 추가됨] 전송 전 최종 검사 (하나라도 틀리면 멈춤)
    // ============================================================
    if (!validators.id(id) || !validators.pw(pw) || !validators.name(name) || 
        !validators.phone(phone) || !validators.email(email)) {
        alert("입력 정보를 다시 확인해주세요.\n빨간색 경고 문구를 확인하세요.");
        return; // 여기서 함수를 끝내서 서버로 안 보냅니다!
    }

    // [기존 코드 유지] 라디오 버튼 값 가져오기
    const isDeafString = document.querySelector('input[name="isDeaf"]:checked').value;
    const isDeafBoolean = (isDeafString === 'true');

    const formData = {
        user_id: id,
        password: pw,
        user_name: name,
        phone_number: phone,
        email: email,
        is_deaf: isDeafBoolean 
    };

    try {
        const response = await fetch(`${BASE_URL}/auth/signup`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (response.ok) {
            alert(data.message);
            window.location.href = "login.html"; 
        } else {
            alert(`가입 실패: ${data.detail}`);
        }
    } catch (error) {
        console.error("Signup Error:", error);
        alert("서버 오류가 발생했습니다.");
    }
}

// 4. 버튼 및 입력창 감시 (Event Listener)
document.addEventListener("DOMContentLoaded", () => {
    const loginBtn = document.getElementById("loginBtn");
    const signupBtn = document.getElementById("signupBtn");

    if (loginBtn) {
        loginBtn.addEventListener("click", handleLogin);
    }
    if (signupBtn) {
        signupBtn.addEventListener("click", handleSignup);
    }

    // ============================================================
    // [3. 추가됨] 입력할 때마다 실시간 검사 (회원가입 페이지용)
    // ============================================================
    // 아이디 입력 감시
    const idInput = document.getElementById("signupId");
    if (idInput) { // 회원가입 페이지에 있을 때만 실행
        idInput.addEventListener("input", (e) => {
            toggleError("signupId", "errorId", validators.id(e.target.value));
        });
    
        document.getElementById("signupPw").addEventListener("input", (e) => {
            toggleError("signupPw", "errorPw", validators.pw(e.target.value));
        });
    
        document.getElementById("signupName").addEventListener("input", (e) => {
            toggleError("signupName", "errorName", validators.name(e.target.value));
        });
    
        document.getElementById("signupPhone").addEventListener("input", (e) => {
            // 숫자만 입력받고 하이픈(-) 자동 추가
            e.target.value = e.target.value
                .replace(/[^0-9]/g, '')
                .replace(/^(\d{0,3})(\d{0,4})(\d{0,4})$/g, "$1-$2-$3").replace(/(\-{1,2})$/g, "");
            toggleError("signupPhone", "errorPhone", validators.phone(e.target.value));
        });
    
        document.getElementById("signupEmail").addEventListener("input", (e) => {
            toggleError("signupEmail", "errorEmail", validators.email(e.target.value));
        });
    }
    // 도우미 함수: "currentId에서 엔터치면 nextId로 커서를 옮겨라!"
    function setupEnterNavigation(currentId, nextId, isLast = false) {
        const currentInput = document.getElementById(currentId);
        
        if (currentInput) { // 해당 입력창이 존재할 때만 실행
            currentInput.addEventListener("keydown", (e) => {
                if (e.key === "Enter") {
                    e.preventDefault(); // 엔터 쳤을 때 폼이 맘대로 전송되는 것 방지
                    
                    if (isLast) {
                        // 마지막 칸(이메일)에서는 엔터치면 '회원가입 버튼'을 클릭!
                        document.getElementById(nextId).click();
                    } else {
                        // 그 외에는 다음 칸으로 포커스 이동
                        const nextInput = document.getElementById(nextId);
                        if (nextInput) nextInput.focus();
                    }
                }
            });
        }
    }

    // 순서대로 사슬처럼 연결하기 (아이디 -> 비번 -> 이름 -> 전화 -> 이메일 -> 완료버튼)
    setupEnterNavigation("signupId", "signupPw");       // 아이디 -> 비번
    setupEnterNavigation("signupPw", "signupName");     // 비번 -> 이름
    setupEnterNavigation("signupName", "signupPhone");  // 이름 -> 전화번호
    setupEnterNavigation("signupPhone", "signupEmail"); // 전화번호 -> 이메일
    
    // 마지막 이메일에서는 엔터치면 -> 회원가입 완료 버튼(signupBtn)로 포커스 이동!
    setupEnterNavigation("signupEmail", "signupBtn", false);
    
    // (로그인 페이지용) 아이디 -> 비번 -> 로그인 버튼
    setupEnterNavigation("loginId", "loginPw");
    setupEnterNavigation("loginPw", "loginBtn", true);
});