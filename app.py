import os
import sys
import subprocess
import threading
from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 전역 상태
is_frozen = getattr(sys, 'frozen', False)
processing_status = {"running": False, "message": ""}

def generate_env_py(url, start_time_raw, end_time_raw, threshold_diff,
                    x_start_percent_raw, x_end_percent_raw,
                    y_start_percent_raw, y_end_percent_raw,
                    transition_stable_sec, base_folder_name):
    """env.py를 생성"""
    base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
    src_dir = os.path.join(base_dir, "src")
    os.makedirs(src_dir, exist_ok=True)

    env_path = os.path.join(src_dir, "env.py")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(f"""from typing import Optional

URL: str = "{url}"
START_TIME_RAW: Optional[str] = {repr(start_time_raw)}
END_TIME_RAW: Optional[str] = {repr(end_time_raw)}
THRESHOLD_DIFF: float = {threshold_diff}
X_START_PERCENT_RAW: float = {x_start_percent_raw}
X_END_PERCENT_RAW: float   = {x_end_percent_raw}
Y_START_PERCENT_RAW: float = {y_start_percent_raw}
Y_END_PERCENT_RAW: float   = {y_end_percent_raw}
TRANSITION_STABLE_SEC: float = {transition_stable_sec}
BASE_FOLDER_NAME: str = "{base_folder_name}"
""")

def run_v3_process():
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

        cmd = [sys.executable, exe_path] if is_python else [exe_path]
        process = subprocess.Popen(
            cmd,
            cwd=src_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            shell=True
        )

        try:
            output, error = process.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            process.kill()
            processing_status.update({"running": False, "message": "5분 초과로 중단됨."})
            return

        if process.returncode == 0:
            processing_status["message"] = "처리 완료. 다운로드 가능."
        else:
            processing_status["message"] = f"오류: {error.strip() or output.strip()}"

    except Exception as e:
        processing_status["message"] = f"예외 발생: {e}"
    finally:
        processing_status["running"] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        form = request.form
        url = form.get('url', '').strip()
        if not url:
            return jsonify({"success": False, "message": "URL 필요"})

        try:
            values = {
                'threshold': float(form.get('threshold', 5.0)),
                'x_start': float(form.get('x_start', 0.0)),
                'x_end': float(form.get('x_end', 100.0)),
                'y_start': float(form.get('y_start', 0.0)),
                'y_end': float(form.get('y_end', 100.0)),
                'transition_sec': float(form.get('transition_sec', 2.0)),
            }
        except ValueError:
            return jsonify({"success": False, "message": "숫자 변환 오류"})

        generate_env_py(
            url=url,
            start_time_raw=form.get('start_time', '0'),
            end_time_raw=form.get('end_time') or None,
            threshold_diff=values['threshold'],
            x_start_percent_raw=values['x_start'],
            x_end_percent_raw=values['x_end'],
            y_start_percent_raw=values['y_start'],
            y_end_percent_raw=values['y_end'],
            transition_stable_sec=values['transition_sec'],
            base_folder_name=form.get('base_folder', 'music_file_')
        )
        return jsonify({"success": True, "message": "설정 저장됨"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/run_process', methods=['POST'])
def run_process():
    if processing_status["running"]:
        return jsonify({"success": False, "message": "이미 실행 중"})
    thread = threading.Thread(target=run_v3_process)
    thread.daemon = True
    thread.start()
    return jsonify({"success": True, "message": "처리 시작"})

@app.route('/check_status')
def check_status():
    return jsonify(processing_status)

@app.route('/download')
def download_output_pdf():
    try:
        base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
        music_folders = []
        for item in os.listdir(base_dir):
            if os.path.isdir(os.path.join(base_dir, item)) and item.startswith("music_file_"):
                try:
                    num = int(item.replace("music_file_", ""))
                    music_folders.append((num, item))
                except ValueError:
                    continue

        if not music_folders:
            return jsonify({"error": "music_file_ 폴더 없음"}), 404

        latest_folder = max(music_folders, key=lambda x: x[0])[1]
        output_pdf = os.path.join(base_dir, latest_folder, "output.pdf")

        if not os.path.exists(output_pdf):
            return jsonify({"error": "output.pdf 없음"}), 404

        return send_file(output_pdf, as_attachment=True, download_name="output.pdf")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)