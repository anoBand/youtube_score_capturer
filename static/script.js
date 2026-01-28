/**
 * static/script.js
 * YouTube 악보 추출기 메인 로직
 */

document.addEventListener('DOMContentLoaded', function() {
    // --- 1. DOM 요소 캐싱 ---
    const elements = {
        url: document.getElementById('url'),
        videoPreview: document.getElementById('videoPreview'),
        selectionArea: document.getElementById('selectionArea'),
        startTime: document.getElementById('start_time'),
        endTime: document.getElementById('end_time'),
        threshold: document.getElementById('threshold'),
        interval: document.getElementById('frame_interval_sec'),
        configForm: document.getElementById('configForm'),
        runBtn: document.getElementById('runBtn'),
        downloadBtn: document.getElementById('downloadBtn'),
        statusArea: document.getElementById('statusArea'),
        statusMessage: document.getElementById('statusMessage'),
        inspectionMode: document.getElementById('inspection_mode'),
        // 모달 관련
        reportModal: document.getElementById('reportModal'),
        openReportBtn: document.getElementById('openReportBtn'),
        closeReportBtn: document.getElementById('closeReportBtn'),
        sendReportBtn: document.getElementById('sendReportBtn'),
        debugInfoArea: document.getElementById('reportDebugInfo'),
        reportDesc: document.getElementById('reportDesc'),
        reportEmail: document.getElementById('reportEmail')
    };

    const coordTypes = ['x_start', 'x_end', 'y_start', 'y_end'];
    const FORMSPREE_ID = 'mdagplqq';
    let pdfObjectURL = null;

    // --- 2. 상태 관리 ---
    const state = {
        isDragging: false,
        startX: 0,
        startY: 0
    };

    // --- 3. 유틸리티 함수 ---
    const utils = {
        extractVideoId: (url) => {
            const regExp = /^.*((youtu.be\/)|(v\/)|(\/u\/\w\/)|(embed\/)|(watch\?))\??v?=?([^#&?]*).*/;
            const match = url.match(regExp);
            return (match && match[7].length === 11) ? match[7] : false;
        },
        updatePreview: () => {
            const vals = {};
            coordTypes.forEach(id => vals[id] = parseInt(document.getElementById(id).value) || 0);

            Object.assign(elements.selectionArea.style, {
                left: `${vals.x_start}%`,
                top: `${vals.y_start}%`,
                width: `${Math.max(0, vals.x_end - vals.x_start)}%`,
                height: `${Math.max(0, vals.y_end - vals.y_start)}%`
            });
        },
        updateInputValue: (id, value) => {
            const input = document.getElementById(id);
            const range = document.getElementById(`${id}_range`);
            if (input) input.value = value;
            if (range) range.value = value;
        },
        showStatus: (msg, type) => {
            const colors = {
                success: '#d4edda',
                error: '#f8d7da',
                processing: '#fff3cd'
            };
            elements.statusArea.style.display = 'block';
            elements.statusArea.style.background = colors[type] || '#eee';
            elements.statusMessage.innerHTML = msg;
        }
    };

    // --- 4. 이벤트 핸들러 ---

    // 유튜브 썸네일 업데이트
    elements.url.addEventListener('input', (e) => {
        const videoId = utils.extractVideoId(e.target.value);
        elements.videoPreview.style.backgroundImage = videoId
            ? `url('https://img.youtube.com/vi/${videoId}/maxresdefault.jpg')`
            : 'none';
    });

    // 좌표 입력 동기화
    coordTypes.forEach(type => {
        const range = document.getElementById(`${type}_range`);
        const num = document.getElementById(type);
        [range, num].forEach(el => el.addEventListener('input', (e) => {
            utils.updateInputValue(type, e.target.value);
            utils.updatePreview();
        }));
    });

    // 드래그 영역 지정
    elements.videoPreview.addEventListener('mousedown', (e) => {
        state.isDragging = true;
        const rect = elements.videoPreview.getBoundingClientRect();
        state.startX = ((e.clientX - rect.left) / rect.width) * 100;
        state.startY = ((e.clientY - rect.top) / rect.height) * 100;
    });

    window.addEventListener('mousemove', (e) => {
        if (!state.isDragging) return;
        const rect = elements.videoPreview.getBoundingClientRect();
        let curX = Math.max(0, Math.min(100, ((e.clientX - rect.left) / rect.width) * 100));
        let curY = Math.max(0, Math.min(100, ((e.clientY - rect.top) / rect.height) * 100));

        utils.updateInputValue('x_start', Math.round(Math.min(state.startX, curX)));
        utils.updateInputValue('x_end', Math.round(Math.max(state.startX, curX)));
        utils.updateInputValue('y_start', Math.round(Math.min(state.startY, curY)));
        utils.updateInputValue('y_end', Math.round(Math.max(state.startY, curY)));
        utils.updatePreview();
    });

    window.addEventListener('mouseup', () => state.isDragging = false);

    // 프레임 미리보기 로드
    async function fetchFrame() {
        const videoId = utils.extractVideoId(elements.url.value);
        if (!videoId || !elements.startTime.value) return;

        elements.videoPreview.style.opacity = '0.5';
        const formData = new FormData();
        formData.append('url', elements.url.value);
        formData.append('start_time', elements.startTime.value);

        try {
            const resp = await fetch('/get_frame', { method: 'POST', body: formData });
            if (resp.ok) {
                const blob = await resp.blob();
                elements.videoPreview.style.backgroundImage = `url('${URL.createObjectURL(blob)}')`;
            }
        } finally {
            elements.videoPreview.style.opacity = '1';
        }
    }

    [elements.startTime, elements.endTime].forEach(el => el.addEventListener('change', fetchFrame));
    elements.url.addEventListener('blur', fetchFrame);

    // 실행 및 다운로드
    elements.configForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        // 유효성 검사
        const thres = parseFloat(elements.threshold.value);
        if (thres < 0.5 || thres > 15.0) return utils.showStatus('감도는 0.5~15 사이여야 합니다.', 'error');

        const interval = parseFloat(elements.interval.value);
        if (interval <= 0 || interval > 3.0) return utils.showStatus('간격은 0.1~3.0초 사이여야 합니다.', 'error');

        if (pdfObjectURL) URL.revokeObjectURL(pdfObjectURL);

        elements.runBtn.disabled = true;
        elements.runBtn.innerHTML = '<span class="loading-spinner"></span> 처리 중...';
        utils.showStatus('분석 중입니다. 잠시만 기다려주세요.', 'processing');

        try {
            const formData = new FormData(this);
            const isInspect = elements.inspectionMode?.checked;
            formData.set('inspection_mode', !!isInspect);

            const response = await fetch('/execute', { method: 'POST', body: formData });
            if (!response.ok) throw new Error((await response.json()).error || '분석 실패');

            const contentType = response.headers.get("content-type");
            if (contentType && contentType.includes("application/json")) {
                const res = await response.json();
                if (res.session_id) {
                    const url = `/inspect/${res.session_id}`;
                    if (!window.open(url, '_blank')) {
                        utils.showStatus(`완료! 팝업 차단됨: <a href="${url}" target="_blank">[여기]</a> 클릭`, 'success');
                    } else {
                        utils.showStatus('새 탭에서 검수 페이지가 열렸습니다.', 'success');
                    }
                }
            } else {
                const blob = await response.blob();
                pdfObjectURL = URL.createObjectURL(blob);
                elements.downloadBtn.disabled = false;
                utils.showStatus('완료되었습니다! 자동으로 다운로드됩니다.', 'success');

                const link = document.createElement('a');
                link.href = pdfObjectURL;
                link.download = 'score.pdf';
                link.click();
            }
        } catch (err) {
            utils.showStatus(`실패: ${err.message}`, 'error');
        } finally {
            elements.runBtn.disabled = false;
            elements.runBtn.innerHTML = '▶️ 실행';
        }
    });

    elements.downloadBtn.addEventListener('click', () => {
        if (!pdfObjectURL) return;
        const a = document.createElement('a');
        a.href = pdfObjectURL;
        a.download = 'score.pdf';
        a.click();
    });

    // --- 5. 초기 상태 설정 ---
    utils.updatePreview();

    // URL 파라미터 복원
    const fields = ['url', 'start_time', 'end_time', 'x_start', 'x_end', 'y_start', 'y_end', 'threshold', 'frame_interval_sec'];
    const params = new URLSearchParams(window.location.search);

    fields.forEach(id => {
        if (params.has(id)) {
            const val = params.get(id);
            const el = document.getElementById(id);
            if (el) {
                el.value = val;
                const range = document.getElementById(`${id}_range`);
                if (range) range.value = val;
                el.dispatchEvent(new Event('input', { bubbles: true }));
            }
        }
    });

    // URL 업데이트 로직 (Debounce 적용 가능)
    function updateURL() {
        const p = new URLSearchParams();
        fields.forEach(id => {
            const val = document.getElementById(id)?.value;
            if (val) p.set(id, val);
        });
        window.history.replaceState({}, '', `?${p.toString()}`);
    }
    fields.forEach(id => document.getElementById(id)?.addEventListener('change', updateURL));

    // --- 6. 버그 제보 모달 ---
    elements.openReportBtn.addEventListener('click', () => {
        const data = {
            url: elements.url.value || 'N/A',
            time: `${elements.startTime.value || '0'}~${elements.endTime.value || '끝'}`,
            x: `${document.getElementById('x_start').value}-${document.getElementById('x_end').value}`,
            y: `${document.getElementById('y_start').value}-${document.getElementById('y_end').value}`,
            agent: navigator.userAgent,
            timeStr: new Date().toLocaleString()
        };
        elements.debugInfoArea.value = `[Info] ${data.timeStr}\nURL: ${data.url}\nRange: ${data.time}\nCropX: ${data.x}, CropY: ${data.y}\nBrowser: ${data.agent}`;
        elements.reportModal.classList.add('open');
    });

    const closeModal = () => elements.reportModal.classList.remove('open');
    elements.closeReportBtn.addEventListener('click', closeModal);
    elements.reportModal.addEventListener('click', (e) => { if(e.target === elements.reportModal) closeModal(); });

    elements.sendReportBtn.addEventListener('click', async () => {
        const msg = elements.reportDesc.value.trim();
        if (!msg) return alert('내용을 입력해주세요.');

        elements.sendReportBtn.textContent = '보내는 중...';
        elements.sendReportBtn.disabled = true;

        try {
            const resp = await fetch(`https://formspree.io/f/${FORMSPREE_ID}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: msg, _replyto: elements.reportEmail.value || 'anon', info: elements.debugInfoArea.value })
            });
            if (resp.ok) {
                alert('전송되었습니다. 감사합니다!');
                closeModal();
            }
        } finally {
            elements.sendReportBtn.textContent = '🚀 전송하기';
            elements.sendReportBtn.disabled = false;
        }
    });

    // Driver.js 가이드 (간소화된 설정)
    if (window.driver) {
        const driver = window.driver.js.driver({
            showProgress: true,
            steps: [
                { element: '#tour-url', popover: { title: 'URL 입력', description: '추출할 영상 주소를 입력하세요.' } },
                { element: '#tour-time', popover: { title: '시간 설정', description: '추출할 구간을 입력하세요.' } },
                { element: '#tour-preview', popover: { title: '영역 지정', description: '마우스 드래그로 악보 범위를 선택하세요.' } }
            ]
        });
        // driver.drive(); // 필요 시 활성화
    }
});