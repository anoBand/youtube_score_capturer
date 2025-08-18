import os
import sys
import subprocess
import threading
import shutil
from flask import Flask, render_template, request, jsonify, send_file, after_this_request
from flask_cors import CORS

app = Flask(__name__)
# 보안 강화를 위해 환경변수에서 비밀 키를 가져오거나, 개발용 기본 키를 사용합니다.
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key')
CORS(app)

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
            "--start-time", params.get('start_time', '0'),
            "--threshold", str(params.get('threshold', 5.0)),
            "--x-start", str(params.get('x_start', 0.0)),
            "--x-end", str(params.get('x_end', 100.0)),
            "--y-start", str(params.get('y_start', 0.0)),
            "--y-end", str(params.get('y_end', 100.0)),
            "--transition-sec", str(params.get('transition_sec', 2.0)),
            "--base-folder", params.get('base_folder', 'music_file_')
        ])
        if params.get('end_time'):
            cmd.extend(["--end-time", params['end_time']])

        process = subprocess.Popen(
            cmd,
            cwd=src_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
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
    try:
        base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
        # 'music_file_'로 시작하는 폴더를 찾아 최신 폴더를 선택합니다.
        music_folders = []
        for item in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, item)) and item.startswith("music_file_"):
                try:
                    # 폴더 이름에서 숫자 부분을 추출하여 정렬 기준으로 삼습니다.
                    num = int(item.replace("music_file_", ""))
                    music_folders.append((num, item))
                except ValueError:
                    continue

        if not music_folders:
            return jsonify({"error": "출력 폴더(music_file_*)를 찾을 수 없습니다."}), 404

        # 숫자 기준으로 가장 큰 폴더(가장 최신)를 찾습니다.
        latest_folder_name = max(music_folders, key=lambda x: x[0])[1]
        output_pdf_path = os.path.join(base_dir, latest_folder_name, "output.pdf")

        if not os.path.exists(output_pdf_path):
            return jsonify({"error": "PDF 파일(output.pdf)을 찾을 수 없습니다."}), 404

        @after_this_request
        def cleanup(response):
            folder_to_delete = os.path.dirname(output_pdf_path)
            try:
                shutil.rmtree(folder_to_delete)
                print(f"Successfully cleaned up {folder_to_delete}")
            except Exception as e:
                print(f"Error during cleanup: {e}")
            return response

        return send_file(output_pdf_path, as_attachment=True, download_name="output.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
