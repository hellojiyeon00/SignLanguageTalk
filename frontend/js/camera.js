// ===== DOM 요소 가져오기 =====
const openBtn = document.getElementById("signCameraBtn");
const closeBtn = document.getElementById("closeCameraBtn");
const modal = document.getElementById("cameraModal");
const overlay = document.getElementById("cameraOverlay");
const video = document.getElementById("videoInput");
const startBtn = document.getElementById("startBtn");
const stopBtn = document.getElementById("stopBtn");
const statusText = document.getElementById("statusText");
const messagesDiv = document.getElementById("messages");

// ===== 상태 및 MediaPipe 변수 =====
let stream = null;
let cameraHelper = null;
let isDetecting = false;

// MediaPipe Holistic 인스턴스 생성
const holistic = new Holistic({
    locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/holistic/${file}`
});

holistic.setOptions({
    modelComplexity: 1,
    smoothLandmarks: true,
    minDetectionConfidence: 0.5,
    minTrackingConfidence: 0.5
});

// ===== 랜드마크 추출 및 전송 함수 =====
holistic.onResults((results) => {
    // 시작 버튼이 눌린 상태에서만 서버로 좌표 전송
    if (!isDetecting) return;

    const extract = (lms, indices) => {
        if (!lms) return new Array(indices.length * 2).fill(0);
        return indices.flatMap(i => [lms[i].x, lms[i].y]);
    };

    const poseIdx = [11, 12, 13, 14, 15, 16]; // 어깨, 팔꿈치, 손목
    const handIdx = Array.from({ length: 21 }, (_, i) => i); // 손가락 전체

    const landmarks = [
        ...extract(results.poseLandmarks, poseIdx),
        ...extract(results.leftHandLandmarks, handIdx),
        ...extract(results.rightHandLandmarks, handIdx)
    ];

    // 서버로 좌표 전송 (이미지 대신 가벼운 리스트 전송)
    socket.emit("sign_landmarks", landmarks);
});

// ===== 📷 카메라 버튼 클릭 → 팝업 열기 =====
openBtn.addEventListener("click", async () => {
    modal.style.display = "block";
    overlay.style.display = "block";

    try {
        // 카메라 스트림 요청
        stream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 },
            audio: false
        });
        video.srcObject = stream;
        statusText.textContent = "카메라 준비 완료";

        // MediaPipe Camera Helper 설정
        cameraHelper = new Camera(video, {
            onFrame: async () => {
                // 카메라 프레임을 계속 Holistic 모델로 전달
                if (isDetecting) await holistic.send({ image: video });
            },
            width: 640,
            height: 480
        });
        cameraHelper.start();

    } catch (err) {
        console.error("Camera error:", err);
        alert("카메라 접근이 거부되었습니다.\n브라우저 설정을 확인해주세요.");
        closeCamera();
    }
});

// ===== ▶️ 시작 버튼 클릭 (분류 시작) =====
startBtn.addEventListener("click", () => {
    isDetecting = true;
    startBtn.disabled = true;
    stopBtn.disabled = false;
    statusText.textContent = "수어 인식 중... 동작을 수행하세요.";
    statusText.classList.add("active");
});

// ===== ⏹️ 종료 버튼 클릭 (분류 중단) =====
stopBtn.addEventListener("click", () => {
    isDetecting = false;
    startBtn.disabled = false;
    stopBtn.disabled = true;
    statusText.textContent = "분석 중... 잠시만 기다려주세요.";
    statusText.classList.remove("active");

    // 서버에 배치 처리(LLM 문장화) 신호 전송
    socket.emit("stop_sign");
});

// ===== ✖ 닫기 버튼 클릭 =====
closeBtn.addEventListener("click", closeCamera);

// ===== 오버레이 클릭 → 팝업 닫기 =====
overlay.addEventListener("click", closeCamera);

// ===== 서버로부터 결과 수신 =====

// 1. 실시간 단어 인식 결과 (중간 피드백용)
socket.on("sign_result", (data) => {
    if (data && data.gloss) {
        addMessageToChat(data.gloss, "interim");
    }
});

// 2. 최종 문장 결과 (LLM 응답)
socket.on("final_sentence", (data) => {
    if (data && data.sentence) {
        addMessageToChat(data.sentence, "final");
        statusText.textContent = "문장 생성 완료!";
    }
});

// ===== 채팅창에 메시지 추가 =====
function addMessageToChat(content, type) {
    const msgDiv = document.createElement("div");
    if (type === "final") {
        msgDiv.className = "message sent final";
        msgDiv.textContent = `📝 ${content}`;
    } else {
        msgDiv.className = "message sent";
        msgDiv.textContent = `🤟 ${content}`;
    }
    messagesDiv.appendChild(msgDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

// ===== 카메라 종료 + 팝업 닫기 =====
function closeCamera() {
    isDetecting = false;

    // 카메라 스트림 종료
    if (stream) {
        stream.getTracks().forEach(track => track.stop());
        stream = null;
    }

    if (cameraHelper) {
        cameraHelper.stop();
        cameraHelper = null;
    }

    // 비디오 초기화
    video.srcObject = null;

    // 팝업 닫기
    modal.style.display = "none";
    overlay.style.display = "none";

    // 상태 초기화
    startBtn.disabled = false;
    stopBtn.disabled = true;
    statusText.textContent = "";
    statusText.classList.remove("active");

    console.log("[CAMERA] 카메라 종료");
}