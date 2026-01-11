/* templates/script.js */

const selectionArea = document.getElementById('selectionArea');
const videoPreview = document.getElementById('videoPreview');
const urlInput = document.getElementById('url');
const coordTypes = ['x_start', 'x_end', 'y_start', 'y_end'];
const startTimeInput = document.getElementById('start_time');

// --- [항목 3] 유튜브 썸네일 로드 로직 ---
function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length == 11) ? match[7] : false;
}

urlInput.addEventListener('input', (e) => {
    const videoId = extractVideoId(e.target.value);
    if (videoId) {
        // 고화질 썸네일(maxresdefault) 시도, 없을 경우를 대비해 배경색 검정 유지
        const thumbUrl = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
        videoPreview.style.backgroundImage = `url('${thumbUrl}')`;
    } else {
        videoPreview.style.backgroundImage = 'none';
    }
});

// [변경] Range와 Number 입력값 동기화 및 프리뷰 업데이트
coordTypes.forEach(type => {
    const rangeInput = document.getElementById(`${type}_range`);
    const numberInput = document.getElementById(type);

    // 슬라이더 변경 시 숫자 칸 업데이트
    rangeInput.addEventListener('input', (e) => {
        numberInput.value = e.target.value;
        updatePreview();
    });

    // 숫자 칸 변경 시 슬라이더 업데이트
    numberInput.addEventListener('input', (e) => {
        rangeInput.value = e.target.value;
        updatePreview();
    });
});

// [항목 4] 실시간 프레임 요청 함수
async function fetchCurrentFrame() {
    const url = urlInput.value;
    const startTime = startTimeInput.value;

    const videoId = extractVideoId(url);
    if (!videoId) return;

    // 사용자에게 로딩 중임을 알림 (투명도 조절 등)
    videoPreview.style.opacity = '0.5';

    const formData = new FormData();
    formData.append('url', url);
    formData.append('start_time', startTime);

    try {
        const response = await fetch('/get_frame', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            const blob = await response.blob();
            const frameUrl = window.URL.createObjectURL(blob);
            videoPreview.style.backgroundImage = `url('${frameUrl}')`;
        }
    } catch (error) {
        console.error('프레임 로드 실패:', error);
    } finally {
        videoPreview.style.opacity = '1';
    }
}

// 시작 시간 입력 칸에서 포커스가 나갈 때(blur) 또는 엔터 칠 때 프레임 갱신
startTimeInput.addEventListener('change', fetchCurrentFrame);

// URL이 입력된 상태에서 시간이 이미 있다면 초기 로드
urlInput.addEventListener('blur', () => {
    if (startTimeInput.value) fetchCurrentFrame();
});

function updatePreview() {
    const vals = {};
    coordTypes.forEach(id => {
        vals[id] = parseInt(document.getElementById(id).value) || 0;
    });

    selectionArea.style.left = vals.x_start + '%';
    selectionArea.style.top = vals.y_start + '%';
    selectionArea.style.width = Math.max(0, vals.x_end - vals.x_start) + '%';
    selectionArea.style.height = Math.max(0, vals.y_end - vals.y_start) + '%';
}

// 초기 호출
updatePreview();

// 실행 및 통신 로직
let pdfObjectURL = null;
const configForm = document.getElementById('configForm');
const runBtn = document.getElementById('runBtn');
const downloadBtn = document.getElementById('downloadBtn');

configForm.addEventListener('submit', async function(e) {
    e.preventDefault();
    if (pdfObjectURL) window.URL.revokeObjectURL(pdfObjectURL);

    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="loading-spinner"></span> 처리 중...';
    showStatus('영상을 분석하여 악보를 추출하고 있습니다.', 'processing');

    try {
        const response = await fetch('/execute', { method: 'POST', body: new FormData(this) });
        if (response.ok) {
            const blob = await response.blob();
            pdfObjectURL = window.URL.createObjectURL(blob);
            downloadBtn.disabled = false;
            showStatus('PDF 생성이 완료되었습니다!', 'success');
        } else {
            const err = await response.json();
            showStatus('실패: ' + (err.error || '알 수 없는 오류'), 'error');
        }
    } catch (error) {
        showStatus('서버 연결 실패: ' + error.message, 'error');
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '▶️ 실행';
    }
});

downloadBtn.addEventListener('click', () => {
    const a = document.createElement('a');
    a.href = pdfObjectURL;
    a.download = 'sheet_music_score.pdf';
    a.click();
});

function showStatus(msg, type) {
    const area = document.getElementById('statusArea');
    area.style.display = 'block';
    area.style.background = type === 'success' ? '#d4edda' : type === 'error' ? '#f8d7da' : '#fff3cd';
    document.getElementById('statusMessage').innerHTML = msg;
}