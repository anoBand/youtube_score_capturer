/**
 * static/inspect.js
 * YouTube Score Capturer - 수동 검수 페이지 로직 (v2.0)
 */

document.addEventListener('DOMContentLoaded', () => {
    console.log("🚀 Inspection script loaded.");

    // DOM 요소 참조 (ID가 없을 경우를 대비해 안전하게 가져옴)
    const container = document.getElementById('inspectionContainer') || document.body;
    const imageGrid = document.getElementById('imageGrid');
    const finalizeBtn = document.getElementById('finalizeBtn');
    const btnContent = document.getElementById('btnContent') || finalizeBtn; // 텍스트만 있는 경우 버튼 자체 사용

    // 1. 세션 ID 추출 (HTML 속성 -> URL 파싱 순으로 시도)
    let sessionId = container.dataset.sessionId;
    if (!sessionId) {
        // URL 예시: /inspect/550e8400-e29b-41d4-a716-446655440000
        const parts = window.location.pathname.split('/');
        sessionId = parts[parts.length - 1];
    }

    if (!sessionId) {
        alert("세션 ID를 찾을 수 없습니다. 페이지를 새로고침 해주세요.");
        console.error("Session ID missing.");
        return;
    }
    console.log("Session ID:", sessionId);

    // 2. 이미지 선택 토글 로직
    if (imageGrid) {
        imageGrid.addEventListener('click', (e) => {
            // 클릭된 요소가 .img-item 자신이거나 그 내부 요소일 경우 탐색
            const item = e.target.closest('.img-item');
            if (item) {
                e.preventDefault(); // 이미지 드래그 등 기본 동작 방지
                item.classList.toggle('selected');
                console.log("Toggled item:", item.dataset.filename, item.classList.contains('selected'));
            }
        });
    } else {
        console.error("Image grid element not found!");
    }

    // 3. 최종 PDF 생성 로직
    async function generatePdf() {
        if (!sessionId) return alert("세션 정보가 없습니다.");

        const selectedNodes = document.querySelectorAll('.img-item.selected');
        const selectedImages = Array.from(selectedNodes).map(n => n.dataset.filename);

        console.log("Selected images:", selectedImages);

        if (selectedImages.length === 0) {
            alert("최소 한 장 이상의 이미지를 선택해야 합니다.");
            return;
        }

        // 버튼 잠금 및 로딩 표시
        if (finalizeBtn) finalizeBtn.disabled = true;
        if (btnContent) btnContent.innerHTML = '<span class="loading-spinner" style="border: 2px solid #fff; border-top-color: transparent; border-radius: 50%; width: 1em; height: 1em; display: inline-block; animation: spin 1s linear infinite; margin-right: 5px;"></span> 생성 중...';

        try {
            const response = await fetch('/finalize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    selected_images: selectedImages
                })
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = "final_score.pdf";
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);

                alert("다운로드가 시작되었습니다! 파일을 확인한 후 이 창을 닫아주세요.");
            } else {
                let errMsg = "PDF 생성 실패";
                try {
                    const errData = await response.json();
                    errMsg = errData.error || errMsg;
                } catch (e) {}
                alert("오류: " + errMsg);
            }
        } catch (err) {
            console.error(err);
            alert("서버 통신 중 오류가 발생했습니다.");
        } finally {
            if (finalizeBtn) finalizeBtn.disabled = false;
            if (btnContent) btnContent.innerText = "PDF 생성 및 다운로드";
        }
    }

    // 버튼 이벤트 연결
    if (finalizeBtn) {
        finalizeBtn.addEventListener('click', generatePdf);
    } else {
        console.error("Finalize button not found!");
    }

    // 로딩 애니메이션 스타일 주입 (인라인)
    const style = document.createElement('style');
    style.innerHTML = `@keyframes spin { to { transform: rotate(360deg); } }`;
    document.head.appendChild(style);
});