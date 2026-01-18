/* templates/script.js */

const selectionArea = document.getElementById('selectionArea');
const videoPreview = document.getElementById('videoPreview');
const urlInput = document.getElementById('url');
const coordTypes = ['x_start', 'x_end', 'y_start', 'y_end'];
const startTimeInput = document.getElementById('start_time');

// --- [항목 3] 유튜브 썸네일 로드 로직 (기존 유지) ---
function extractVideoId(url) {
    const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[7].length === 11) ? match[7] : false;
}

urlInput.addEventListener('input', (e) => {
    const videoId = extractVideoId(e.target.value);
    if (videoId) {
        const thumbUrl = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
        videoPreview.style.backgroundImage = `url('${thumbUrl}')`;
    } else {
        videoPreview.style.backgroundImage = 'none';
    }
});

// --- [기존] Range와 Number 입력값 동기화 및 프리뷰 업데이트 ---
coordTypes.forEach(type => {
    const rangeInput = document.getElementById(`${type}_range`);
    const numberInput = document.getElementById(type);

    rangeInput.addEventListener('input', (e) => {
        numberInput.value = e.target.value;
        updatePreview();
    });

    numberInput.addEventListener('input', (e) => {
        rangeInput.value = e.target.value;
        updatePreview();
    });
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

// --- [추가] 마우스 드래그로 영역 선택 기능 ---
let isDragging = false;
let startXPercent = 0;
let startYPercent = 0;

// 1. 드래그 시작 (MouseDown)
videoPreview.addEventListener('mousedown', (e) => {
    isDragging = true;
    const rect = videoPreview.getBoundingClientRect();

    // 클릭한 위치를 % 단위로 계산 (0~100)
    startXPercent = ((e.clientX - rect.left) / rect.width) * 100;
    startYPercent = ((e.clientY - rect.top) / rect.height) * 100;

    // 범위를 벗어나지 않도록 클램핑
    startXPercent = Math.max(0, Math.min(100, startXPercent));
    startYPercent = Math.max(0, Math.min(100, startYPercent));
});

// 2. 드래그 중 (MouseMove)
window.addEventListener('mousemove', (e) => {
    if (!isDragging) return;

    const rect = videoPreview.getBoundingClientRect();
    let currentXPercent = ((e.clientX - rect.left) / rect.width) * 100;
    let currentYPercent = ((e.clientY - rect.top) / rect.height) * 100;

    // 범위 제한 (0~100)
    currentXPercent = Math.max(0, Math.min(100, currentXPercent));
    currentYPercent = Math.max(0, Math.min(100, currentYPercent));

    // 시작점과 현재점 중 작은 값이 Start, 큰 값이 End가 됨 (역방향 드래그 지원)
    const xStart = Math.round(Math.min(startXPercent, currentXPercent));
    const xEnd = Math.round(Math.max(startXPercent, currentXPercent));
    const yStart = Math.round(Math.min(startYPercent, currentYPercent));
    const yEnd = Math.round(Math.max(startYPercent, currentYPercent));

    // 입력 필드(Range, Number) 값 업데이트
    updateInputValue('x_start', xStart);
    updateInputValue('x_end', xEnd);
    updateInputValue('y_start', yStart);
    updateInputValue('y_end', yEnd);

    // 프리뷰 박스 즉시 갱신
    updatePreview();
});

// 3. 드래그 종료 (MouseUp)
window.addEventListener('mouseup', () => {
    isDragging = false;
});

// 헬퍼 함수: ID를 받아 Range와 Number input 둘 다 업데이트
function updateInputValue(id, value) {
    document.getElementById(id).value = value;
    document.getElementById(`${id}_range`).value = value;
}


// --- [항목 4] 실시간 프레임 요청 함수 (기존 유지) ---
async function fetchCurrentFrame() {
    const url = urlInput.value;
    const startTime = startTimeInput.value;
    const videoId = extractVideoId(url);
    if (!videoId) return;

    videoPreview.style.opacity = '0.5';
    const formData = new FormData();
    formData.append('url', url);
    formData.append('start_time', startTime);

    try {
        const response = await fetch('/get_frame', { method: 'POST', body: formData });
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

startTimeInput.addEventListener('change', fetchCurrentFrame);
urlInput.addEventListener('blur', () => {
    if (startTimeInput.value) fetchCurrentFrame();
});

// 초기 호출
updatePreview();

// --- 실행 및 통신 로직 (기존 유지) ---
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

            // 1. 수동 다운로드 버튼 활성화 (기존 로직 유지)
            downloadBtn.disabled = false;

            // 2. 상태 메시지 업데이트
            showStatus('PDF 생성이 완료되었습니다 (자동 다운로드). 다운로드 버튼을 눌러 받을 수도 있습니다!', 'success');

            // [추가] 3. 자동 다운로드 트리거 실행
            const autoDownloadLink = document.createElement('a');
            autoDownloadLink.href = pdfObjectURL;
            autoDownloadLink.download = 'sheet_music_score.pdf'; // 저장될 파일명
            document.body.appendChild(autoDownloadLink); // 파이어폭스 등 호환성 위해 바디에 추가
            autoDownloadLink.click(); // 강제 클릭 발생
            document.body.removeChild(autoDownloadLink); // 클릭 후 제거

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

document.addEventListener('DOMContentLoaded', () => {
    const driverObj = window.driver.js.driver({
        showProgress: true,
        animate: true,
        allowClose: true,  // 배경 클릭 또는 ESC로 종료 허용
        doneBtnText: '완료',
        nextBtnText: '다음',
        prevBtnText: '이전',

        // [중요] 팝오버가 렌더링될 때 '건너뛰기' 버튼을 강제로 주입
        onPopoverRender: (popover, { config, state }) => {
            // footer 요소 찾기 (라이브러리 내부 클래스명)
            const footer = popover.wrapper.querySelector('.driver-popover-footer');

            // 이미 건너뛰기 버튼이 있다면 중복 생성 방지
            if (footer && !footer.querySelector('.skip-btn')) {
                const skipBtn = document.createElement('button');
                skipBtn.innerText = '건너뛰기';
                skipBtn.className = 'skip-btn';

                // 스타일 직접 지정 (왼쪽에 배치)
                skipBtn.style.cssText = `
                    background: none; 
                    border: none; 
                    color: #888; 
                    text-decoration: underline; 
                    font-size: 12px; 
                    cursor: pointer; 
                    margin-right: auto; /* 우측 버튼들과 간격 벌리기 (Flexbox) */
                    padding: 5px;
                `;

                skipBtn.onclick = () => {
                    driverObj.destroy(); // 투어 종료
                };

                // footer의 가장 앞에 버튼 추가
                footer.prepend(skipBtn);
            }
        },

        steps: [
            {
                element: '#tour-url',
                popover: {
                    title: '1. 영상 주소 입력',
                    description: '악보를 추출할 YouTube 영상의 URL을 여기에 붙여넣으세요.',
                    side: "bottom", align: 'start'
                }
            },
            {
                element: '#tour-time',
                popover: {
                    title: '2. 시간 설정',
                    description: '추출을 시작할 시간과 종료할 시간을 입력합니다.',
                    side: "bottom", align: 'start'
                }
            },
            {
                element: '#tour-preview',
                popover: {
                    title: '3. 영역 지정',
                    description: '이 박스를 <strong>마우스로 드래그</strong>하여 악보 영역을 파란색 박스로 감싸주세요.<br>하단에서 세부적으로 조정할 수 있습니다.',
                    side: "top", align: 'start'
                }
            },
            {
                element: '#tour-advanced',
                popover: {
                    title: '4. 고급 설정',
                    description: '감도와 처리 간격입니다.<br>일반적으로는 <strong>수정할 필요가 없습니다.</strong>',
                    side: "top", align: 'start'
                }
            }
        ]
    });

    driverObj.drive();
});