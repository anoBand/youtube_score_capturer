import os
import sys
import subprocess
import threading
import shutil
import time
import tempfile
import logging
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS

app = Flask(__name__)
# 보안 강화를 위해 환경변수에서 비밀 키를 가져오거나, 개발용 기본 키를 사용합니다.
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
CORS(app)

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# 전역 락 객체
download_lock = threading.RLock()

# 전역 상태
is_frozen = getattr(sys, 'frozen', False)
processing_status = {"running": False, "message": ""}

def run_v3_process(params):
    global processing_status
    try:
        processing_status.update({"running": True, "message": "처리 중..."})
        base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
        src_dir = os.path.join(base_dir, "src")

        possible_files = ["v3.exe", "v3.py", "main.exe", "main.py"]
        exe_path, is_python = None, False
        for name in possible_files:
            path = os.path.join(src_dir, name)
            if os.path.exists(path):
                exe_path = path
                is_python = name.endswith(".py")
                break

        if not exe_path:
            processing_status.update({"running": False, "message": "실행 파일을 찾을 수 없습니다."})
            return

        # v3.py에 전달할 커맨드 라인 인자를 구성합니다.
        cmd = [sys.executable, exe_path] if is_python else [exe_path]
        cmd.extend([
            "--url", params['url'],
            "--start-time", params.get('start_time') or '0',
            "--threshold", str(params.get('threshold') or 5.0),
            "--x-start", str(params.get('x_start') or 0.0),
            "--x-end", str(params.get('x_end') or 100.0),
            "--y-start", str(params.get('y_start') or 0.0),
            "--y-end", str(params.get('y_end') or 100.0),
            "--transition-sec", str(params.get('transition_sec') or 2.0),
            "--base-folder", params.get('base_folder') or 'music_file_'
        ])
        end_time = params.get('end_time')
        if end_time:
            cmd.extend(["--end-time", end_time])

        process = subprocess.Popen(
            cmd,
            cwd=src_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='cp949', # utf-8에서 cp949로 변경
            # shell=True는 보안상 위험하므로 사용하지 않습니다.
            shell=False
        )

        try:
            output, error = process.communicate(timeout=300) # 5분 타임아웃
        except subprocess.TimeoutExpired:
            process.kill()
            processing_status.update({"running": False, "message": "오류: 처리 시간이 5분을 초과하여 중단되었습니다."})
            return

        if process.returncode == 0:
            processing_status["message"] = "처리 완료. PDF 파일을 다운로드할 수 있습니다."
        else:
            # 사용자에게 보여줄 오류 메시지를 정리합니다.
            error_message = (error or output or "알 수 없는 오류가 발생했습니다.").strip()
            processing_status["message"] = f"오류 발생: {error_message}"

    except Exception as e:
        processing_status["message"] = f"예외 발생: {e}"
    finally:
        processing_status["running"] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_process', methods=['POST'])
def run_process():
    if processing_status["running"]:
        return jsonify({"success": False, "message": "이미 다른 프로세스가 실행 중입니다."})

    form_data = request.form
    url = form_data.get('url', '').strip()
    if not url:
        return jsonify({"success": False, "message": "YouTube URL을 입력해야 합니다."})

    # 받은 폼 데이터를 스레드에 전달
    thread = threading.Thread(target=run_v3_process, args=(form_data,))
    thread.daemon = True
    thread.start()
    return jsonify({"success": True, "message": "프로세스 실행을 시작했습니다."})

@app.route('/check_status')
def check_status():
    return jsonify(processing_status)

@app.route('/download')
def download_output_pdf():
    """PDF 파일을 다운로드하고 안전하게 정리하는 함수"""
    try:
        with download_lock:
            base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
            
            # 최신 music_file 폴더 찾기
            latest_folder_path = find_latest_music_folder(base_dir)
            if not latest_folder_path:
                logging.warning("출력 폴더(music_file_*)를 찾을 수 없습니다.")
                return jsonify({"error": "출력 폴더를 찾을 수 없습니다."}), 404

            output_pdf_path = os.path.join(latest_folder_path, "output.pdf")
            
            if not os.path.exists(output_pdf_path):
                logging.warning(f"PDF 파일을 찾을 수 없습니다: {output_pdf_path}")
                return jsonify({"error": "PDF 파일을 찾을 수 없습니다."}), 404

            # 임시 파일로 복사하여 안전하게 전송
            temp_pdf_path = create_temp_copy(output_pdf_path)
            
            @after_this_request
            def cleanup(response):
                """응답 완료 후 정리 작업"""
                cleanup_thread = threading.Thread(
                    target=safe_cleanup, 
                    args=(latest_folder_path, temp_pdf_path),
                    daemon=True
                )
                cleanup_thread.start()
                return response

            return send_file(
                temp_pdf_path, 
                as_attachment=True, 
                download_name="output.pdf",
                mimetype='application/pdf'
            )

    except Exception as e:
        logging.error(f"PDF 다운로드 중 오류 발생: {str(e)}")
        return jsonify({"error": "파일 다운로드 중 오류가 발생했습니다."}), 500


def find_latest_music_folder(base_dir):
    """가장 최신의 music_file 폴더를 찾는 함수"""
    music_folders = []
    
    try:
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path) and item.startswith("music_file_"):
                try:
                    # 폴더 이름에서 숫자 추출
                    num_str = item.replace("music_file_", "")
                    num = int(num_str)
                    music_folders.append((num, item_path))
                except ValueError as e:
                    logging.warning(f"폴더 이름 파싱 실패: {item}, 오류: {e}")
                    continue

        if not music_folders:
            return None

        # 가장 큰 숫자의 폴더 반환
        return max(music_folders, key=lambda x: x[0])[1]
        
    except OSError as e:
        logging.error(f"디렉토리 접근 오류: {base_dir}, 오류: {e}")
        return None


def create_temp_copy(source_path):
    """임시 파일로 복사하는 함수"""
    try:
        # 임시 파일 생성
        temp_fd, temp_path = tempfile.mkstemp(suffix='.pdf', prefix='download_')
        os.close(temp_fd)  # 파일 디스크립터 닫기
        
        # 원본 파일을 임시 파일로 복사
        shutil.copy2(source_path, temp_path)
        logging.info(f"임시 파일 생성됨: {temp_path}")
        
        return temp_path
    except Exception as e:
        logging.error(f"임시 파일 생성 실패: {e}")
        raise


def safe_cleanup(folder_path, temp_file_path):
    """안전한 정리 작업을 수행하는 함수"""
    import time
    
    try:
        # 파일 전송 완료를 위한 충분한 대기시간
        time.sleep(10)
        
        # 임시 파일 삭제
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
            logging.info(f"임시 파일 삭제됨: {temp_file_path}")
        
        # 원본 폴더 삭제
        if os.path.exists(folder_path):
            shutil.rmtree(folder_path)
            logging.info(f"폴더 삭제됨: {folder_path}")
            
    except Exception as e:
        logging.error(f"정리 작업 중 오류 발생: {e}")