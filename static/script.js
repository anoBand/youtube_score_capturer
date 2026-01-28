document.addEventListener('DOMContentLoaded', function() {
    // --- Original script.js content ---
    const selectionArea = document.getElementById('selectionArea');
    const videoPreview = document.getElementById('videoPreview');
    const urlInput = document.getElementById('url');
    const coordTypes = ['x_start', 'x_end', 'y_start', 'y_end'];
    const startTimeInput = document.getElementById('start_time');
    const endTimeInput = document.getElementById('end_time');

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

    let isDragging = false;
    let startXPercent = 0;
    let startYPercent = 0;

    videoPreview.addEventListener('mousedown', (e) => {
        isDragging = true;
        const rect = videoPreview.getBoundingClientRect();
        startXPercent = ((e.clientX - rect.left) / rect.width) * 100;
        startYPercent = ((e.clientY - rect.top) / rect.height) * 100;
        startXPercent = Math.max(0, Math.min(100, startXPercent));
        startYPercent = Math.max(0, Math.min(100, startYPercent));
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const rect = videoPreview.getBoundingClientRect();
        let currentXPercent = ((e.clientX - rect.left) / rect.width) * 100;
        let currentYPercent = ((e.clientY - rect.top) / rect.height) * 100;
        currentXPercent = Math.max(0, Math.min(100, currentXPercent));
        currentYPercent = Math.max(0, Math.min(100, currentYPercent));

        const xStart = Math.round(Math.min(startXPercent, currentXPercent));
        const xEnd = Math.round(Math.max(startXPercent, currentXPercent));
        const yStart = Math.round(Math.min(startYPercent, currentYPercent));
        const yEnd = Math.round(Math.max(startYPercent, currentYPercent));

        updateInputValue('x_start', xStart);
        updateInputValue('x_end', xEnd);
        updateInputValue('y_start', yStart);
        updateInputValue('y_end', yEnd);
        updatePreview();
    });

    window.addEventListener('mouseup', () => {
        isDragging = false;
    });

    function updateInputValue(id, value) {
        document.getElementById(id).value = value;
        document.getElementById(`${id}_range`).value = value;
    }

    async function fetchCurrentFrame(timeStr) {
        const url = urlInput.value;
        const targetTime = (typeof timeStr === 'string' && timeStr.trim() !== '') ? timeStr : startTimeInput.value;
        const videoId = extractVideoId(url);
        if (!videoId || !targetTime) return;

        videoPreview.style.opacity = '0.5';
        const formData = new FormData();
        formData.append('url', url);
        formData.append('start_time', targetTime);

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

    startTimeInput.addEventListener('change', (e) => fetchCurrentFrame(e.target.value));
    endTimeInput.addEventListener('change', (e) => fetchCurrentFrame(e.target.value));
    urlInput.addEventListener('blur', () => {
        if (startTimeInput.value) fetchCurrentFrame(startTimeInput.value);
    });

    updatePreview();

    let pdfObjectURL = null;
    const configForm = document.getElementById('configForm');
    const runBtn = document.getElementById('runBtn');
    const downloadBtn = document.getElementById('downloadBtn');

    configForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Add validation for threshold here
        const thresholdInput = document.getElementById('threshold');
        const thresholdValue = parseFloat(thresholdInput.value);

        if (isNaN(thresholdValue) || thresholdValue < 0.5 || thresholdValue > 15.0) {
            showStatus('감도는 0.5에서 15 사이어야 합니다', 'error');
            thresholdInput.focus();
            return; // Prevent form submission
        }

        // New validation for frame_interval_sec
        const frameIntervalInput = document.getElementById('frame_interval_sec');
        const frameIntervalValue = parseFloat(frameIntervalInput.value);

        if (isNaN(frameIntervalValue) || frameIntervalValue <= 0 || frameIntervalValue > 3.0) { // Added <=0 to match existing number input min="0" and step="0.1"
            showStatus('처리 간격은 3초를 넘을 수 없습니다', 'error');
            frameIntervalInput.focus();
            return; // Prevent form submission
        }

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
                showStatus('PDF 생성이 완료되었습니다 (자동 다운로드). 다운로드 버튼을 눌러 받을 수도 있습니다!', 'success');

                const autoDownloadLink = document.createElement('a');
                autoDownloadLink.href = pdfObjectURL;
                autoDownloadLink.download = 'sheet_music_score.pdf';
                document.body.appendChild(autoDownloadLink);
                autoDownloadLink.click();
                document.body.removeChild(autoDownloadLink);
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

    // --- Driver.js tour ---
    const driverObj = window.driver.js.driver({
        showProgress: true,
        animate: true,
        allowClose: true,
        doneBtnText: '완료',
        nextBtnText: '다음',
        prevBtnText: '이전',
        steps: [
            { element: '#tour-url', popover: { title: '1. 영상 주소 입력', description: '악보를 추출할 YouTube 영상의 URL을 여기에 붙여넣으세요.', side: "bottom", align: 'start' } },
            { element: '#tour-time', popover: { title: '2. 시간 설정', description: '추출을 시작할 시간과 종료할 시간을 입력합니다.', side: "bottom", align: 'start' } },
            { element: '#tour-preview', popover: { title: '3. 영역 지정', description: '이 박스를 <strong>마우스로 드래그</strong>하여 악보 영역을 파란색 박스로 감싸주세요.<br>하단에서 세부적으로 조정할 수 있습니다.', side: "top", align: 'start' } },
            { element: '#tour-advanced', popover: { title: '4. 고급 설정', description: '감도와 처리 간격입니다.<br>일반적으로는 <strong>수정할 필요가 없습니다.</strong>', side: "top", align: 'start' } }
        ]
    });
    driverObj.drive();

    // --- Logic from inline script in index.html ---

    // URL State Management
    const fields = [
        'url', 'start_time', 'end_time',
        'x_start', 'x_end', 'y_start', 'y_end',
        'threshold', 'frame_interval_sec'
    ];
    const params = new URLSearchParams(window.location.search);
    let restored = false;

    fields.forEach(id => {
        const element = document.getElementById(id);
        if (element && params.has(id)) {
            element.value = params.get(id);
            restored = true;
            const rangeElement = document.getElementById(id + '_range');
            if (rangeElement) rangeElement.value = params.get(id);
        }
    });

    function updateURL() {
        const newParams = new URLSearchParams();
        fields.forEach(id => {
            const element = document.getElementById(id);
            if (element && element.value) newParams.set(id, element.value);
        });
        window.history.replaceState({}, '', '?' + newParams.toString());
    }

    fields.forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updateURL);
            element.addEventListener('change', updateURL);
        }
    });

    if (restored) {
        setTimeout(() => {
            fields.forEach(id => {
                const element = document.getElementById(id);
                if (element) {
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        }, 100);
    }

    // Error Reporting Modal Logic
    const reportModal = document.getElementById('reportModal');
    const openReportBtn = document.getElementById('openReportBtn');
    const closeReportBtn = document.getElementById('closeReportBtn');
    const sendReportBtn = document.getElementById('sendReportBtn');
    const debugInfoArea = document.getElementById('reportDebugInfo');
    const FORMSPREE_ID = 'mdagplqq';


    openReportBtn.addEventListener('click', () => {
        const data = {
            url: document.getElementById('url').value || '(비어있음)',
            time: `${document.getElementById('start_time').value || '0'} ~ ${document.getElementById('end_time').value || 'end'}`,
            crop_x: `Start: ${document.getElementById('x_start').value}, End: ${document.getElementById('x_end').value}`,
            crop_y: `Start: ${document.getElementById('y_start').value}, End: ${document.getElementById('y_end').value}`,
            threshold: document.getElementById('threshold').value,
            interval: document.getElementById('frame_interval_sec').value,
            userAgent: navigator.userAgent,
            timestamp: new Date().toLocaleString()
        };
        const formattedInfo =
`[시스템 및 입력 정보]
- 타임스탬프: ${data.timestamp}
- YouTube URL: ${data.url}
- 구간: ${data.time}
- X축 설정: ${data.crop_x}
- Y축 설정: ${data.crop_y}
- 감도(Threshold): ${data.threshold}
- 간격(Interval): ${data.interval}
- 브라우저: ${data.userAgent}`;
        debugInfoArea.value = formattedInfo;
        reportModal.classList.add('open');
    });

    const closeModal = () => reportModal.classList.remove('open');
    closeReportBtn.addEventListener('click', closeModal);
    reportModal.addEventListener('click', (e) => {
        if (e.target === reportModal) closeModal();
    });

    // 3. 안전한 익명 전송 (HTTP POST)
    sendReportBtn.addEventListener('click', () => {
        const desc = document.getElementById('reportDesc').value.trim();
        if (!desc) {
            alert('문제 설명을 간단히라도 적어주세요! 😢');
            document.getElementById('reportDesc').focus();
            return;
        }

        const email = document.getElementById('reportEmail').value.trim();
        const debugInfo = debugInfoArea.value;

        // 전송 중 상태 표시
        sendReportBtn.textContent = '보내는 중...';
        sendReportBtn.disabled = true;

        // Formspree API로 전송 (mailto 대체)
        fetch(`https://formspree.io/f/${FORMSPREE_ID}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: desc,
                _replyto: email ? email : "anonymous@report.com", // 회신용 이메일 필드
                debug_info: debugInfo
            })
        })
        .then(response => {
            if (response.ok) {
                alert('소중한 의견이 안전하게 전달되었습니다! 🚀\n감사합니다.');
                document.getElementById('reportDesc').value = ''; // 내용 초기화
                closeModal();
            } else {
                alert('전송에 실패했습니다. 잠시 후 다시 시도해주세요.');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('네트워크 오류가 발생했습니다.');
        })
        .finally(() => {
            // 버튼 상태 복구
            sendReportBtn.textContent = '🚀 전송하기';
            sendReportBtn.disabled = false;
        });
    });
});