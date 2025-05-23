import os
import sys
import subprocess
import threading
import time
from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for
from werkzeug.utils import secure_filename
import zipfile
import tempfile
from typing import Optional

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# 전역 변수
is_frozen = getattr(sys, 'frozen', False)
processing_status = {"running": False, "message": ""}

def generate_env_py(
    url: str,
    start_time_raw: str,
    end_time_raw: str,
    threshold_diff: float,
    x_start_percent_raw: float,
    x_end_percent_raw: float,
    y_start_percent_raw: float,
    y_end_percent_raw: float,
    transition_stable_sec: float,
    base_folder_name: str
):
    """env.py를 생성(또는 갱신)해주는 함수 (src 폴더 내부에 생성)"""
    base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
    src_dir = os.path.join(base_dir, "src")
    
    # src 디렉토리가 없으면 생성
    if not os.path.exists(src_dir):
        os.makedirs(src_dir)
    
    env_path = os.path.join(src_dir, "env.py")

    with open(env_path, "w", encoding="utf-8") as f:
        f.write(
f"""from typing import Optional, List

URL: str = "{url}"

# 동영상 분석 구간 (초 단위)
START_TIME_RAW: Optional[str] = {repr(start_time_raw)} # 정수 입력 시 초로 인식 (기본 처음부터)
END_TIME_RAW: Optional[str] = {repr(end_time_raw)}     # mm:ss 형식 입력 가능, None 입력 시 끝까지

# 프레임 비교 임계값(중복 제거)
THRESHOLD_DIFF: float = {threshold_diff}

# 잘라낼 영역 퍼센트(0% ~ 100%)
X_START_PERCENT_RAW: float = {x_start_percent_raw}
X_END_PERCENT_RAW: float   = {x_end_percent_raw}
Y_START_PERCENT_RAW: float = {y_start_percent_raw}
Y_END_PERCENT_RAW: float   = {y_end_percent_raw}

# 전환 안정화 시간 (초)
TRANSITION_STABLE_SEC: float = {transition_stable_sec}

# 출력 폴더명 접두어
BASE_FOLDER_NAME: str = "{base_folder_name}"

# v3에서 사용하지 않는 변수들 (호환성 유지용)
TAB_REGION_RATIO: float = 0.45  # v1 전용, v3에서는 사용 안함
"""
        )

def run_v3_process():
    """v3.exe를 백그라운드에서 실행"""
    global processing_status
    
    try:
        processing_status["running"] = True
        processing_status["message"] = "처리 중..."
        
        # 실행 위치 설정
        base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
        src_dir = os.path.join(base_dir, "src")
        exe_path = os.path.join(src_dir, "v3.exe")

        if not os.path.exists(exe_path):
            processing_status["message"] = f"오류: {exe_path} 파일이 존재하지 않습니다!"
            processing_status["running"] = False
            return

        # 환경변수(PATH)에 src 추가
        new_env = dict(os.environ)
        new_env["PATH"] = src_dir + os.pathsep + new_env["PATH"]

        # v3.exe 실행 (출력 캡처)
        process = subprocess.Popen(
            [exe_path],
            env=new_env,
            cwd=src_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )

        # 프로세스 완료 대기
        output, _ = process.communicate()
        
        if process.returncode == 0:
            processing_status["message"] = "처리 완료! 파일을 다운로드할 수 있습니다."
        else:
            processing_status["message"] = f"처리 중 오류 발생: {output}"
            
    except Exception as e:
        processing_status["message"] = f"실행 중 오류: {str(e)}"
    finally:
        processing_status["running"] = False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_config', methods=['POST'])
def save_config():
    try:
        # 폼 데이터 가져오기
        url = request.form.get('url', '').strip()
        start_time = request.form.get('start_time', '').strip()
        end_time = request.form.get('end_time', '').strip()
        threshold = request.form.get('threshold', '').strip()
        x_start = request.form.get('x_start', '').strip()
        x_end = request.form.get('x_end', '').strip()
        y_start = request.form.get('y_start', '').strip()
        y_end = request.form.get('y_end', '').strip()
        transition_sec = request.form.get('transition_sec', '').strip()
        base_folder = request.form.get('base_folder', '').strip()

        # 필수값 체크
        if not url:
            return jsonify({"success": False, "message": "YouTube URL을 입력하세요!"})

        try:
            # 숫자 변환 (기본값 처리)
            threshold_val = float(threshold) if threshold else 5.0
            x_start_val = float(x_start) if x_start else 0.0
            x_end_val = float(x_end) if x_end else 100.0
            y_start_val = float(y_start) if y_start else 70.0
            y_end_val = float(y_end) if y_end else 100.0
            transition_val = float(transition_sec) if transition_sec else 2.0
        except ValueError:
            return jsonify({"success": False, "message": "숫자형 변환이 필요한 값들 중 잘못된 입력이 있습니다."})

        # end_time이 비어있다면 None 처리
        end_time_val = None if not end_time else end_time

        # env.py 작성
        generate_env_py(
            url=url,
            start_time_raw=start_time or "0",
            end_time_raw=end_time_val,
            threshold_diff=threshold_val,
            x_start_percent_raw=x_start_val,
            x_end_percent_raw=x_end_val,
            y_start_percent_raw=y_start_val,
            y_end_percent_raw=y_end_val,
            transition_stable_sec=transition_val,
            base_folder_name=base_folder or "music_file_"
        )

        return jsonify({"success": True, "message": "설정이 저장되었습니다!"})

    except Exception as e:
        return jsonify({"success": False, "message": f"저장 중 오류 발생: {str(e)}"})

@app.route('/run_process', methods=['POST'])
def run_process():
    global processing_status
    
    if processing_status["running"]:
        return jsonify({"success": False, "message": "이미 처리 중입니다."})
    
    # 백그라운드에서 v3.exe 실행
    thread = threading.Thread(target=run_v3_process)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "처리를 시작했습니다."})

@app.route('/check_status')
def check_status():
    return jsonify(processing_status)

@app.route('/download')
def download_files():
    try:
        base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
        src_dir = os.path.join(base_dir, "src")
        
        # 생성된 파일들을 찾기 (music_file_로 시작하는 폴더)
        output_folders = []
        for item in os.listdir(src_dir):
            item_path = os.path.join(src_dir, item)
            if os.path.isdir(item_path) and item.startswith("music_file_"):
                output_folders.append(item_path)
        
        if not output_folders:
            return jsonify({"error": "다운로드할 파일이 없습니다. 먼저 처리를 완료해주세요."}), 404
        
        # 임시 ZIP 파일 생성
        temp_dir = tempfile.mkdtemp()
        zip_path = os.path.join(temp_dir, "output_files.zip")
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for folder_path in output_folders:
                folder_name = os.path.basename(folder_path)
                for root, dirs, files in os.walk(folder_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        # ZIP 내부 경로 설정
                        arcname = os.path.join(folder_name, os.path.relpath(file_path, folder_path))
                        zipf.write(file_path, arcname)
        
        return send_file(zip_path, as_attachment=True, download_name="output_files.zip")
        
    except Exception as e:
        return jsonify({"error": f"다운로드 중 오류 발생: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)