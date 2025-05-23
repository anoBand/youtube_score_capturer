import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
from PIL import Image, ImageTk

is_frozen = getattr(sys, 'frozen', False)

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
    env_path = os.path.join(src_dir, "env.py")  # src/env.py로 저장

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

def run_v3():
    """v3.exe를 CMD 창에서 실행"""
    # 실행 위치 설정
    base_dir = os.path.dirname(os.path.abspath(sys.executable if is_frozen else __file__))
    src_dir = os.path.join(base_dir, "src")
    exe_path = os.path.join(src_dir, "v3.exe")

    if not os.path.exists(exe_path):
        messagebox.showerror("오류", f"{exe_path} 파일이 존재하지 않습니다!")
        return

    # 환경변수(PATH)에 src 추가 (예: ffmpeg.exe 사용 시)
    new_env = dict(os.environ)
    new_env["PATH"] = src_dir + os.pathsep + new_env["PATH"]

    # CMD 창으로 실행 (창 유지하려면 /k 사용)
    subprocess.Popen(
        ["cmd", "/k", exe_path],
        env=new_env,
        cwd=src_dir
    )

def save_env():
    # 입력값 가져오기
    url = entry_url.get().strip()
    start_time = entry_start_time.get().strip()
    end_time = entry_end_time.get().strip()
    threshold = entry_threshold.get().strip()
    x_start = entry_xstart.get().strip()
    x_end = entry_xend.get().strip()
    y_start = entry_ystart.get().strip()
    y_end = entry_yend.get().strip()
    transition_sec = entry_transition.get().strip()
    base_folder = entry_base_folder.get().strip()

    # 필수값 체크
    if not url:
        messagebox.showerror("오류", "YouTube URL을 입력하세요!")
        return

    try:
        # 숫자 변환 (기본값 있을 경우 처리 가능)
        threshold_val = float(threshold) if threshold else 5.0
        x_start_val = float(x_start) if x_start else 0.0
        x_end_val = float(x_end) if x_end else 100.0
        y_start_val = float(y_start) if y_start else 70.0
        y_end_val = float(y_end) if y_end else 100.0
        transition_val = float(transition_sec) if transition_sec else 2.0
    except ValueError:
        messagebox.showerror("오류", "숫자형 변환이 필요한 값들 중 잘못된 입력이 있습니다.")
        return

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

    messagebox.showinfo("저장 완료", "설정이 저장되었습니다! 이제 '실행' 버튼을 눌러주세요.")

# GUI 생성
root = tk.Tk()
root.title("YouTube Tab Image Extractor v3")
root.geometry("500x600")

# 메인 프레임
main_frame = tk.Frame(root, padx=20, pady=20)
main_frame.pack(fill="both", expand=True)

# 제목
title_label = tk.Label(main_frame, text="YouTube 악보 추출기 v3", font=("Arial", 16, "bold"))
title_label.pack(pady=(0, 20))

# URL 입력
tk.Label(main_frame, text="YouTube URL:", font=("Arial", 10, "bold")).pack(anchor="w")
entry_url = tk.Entry(main_frame, width=60)
entry_url.pack(fill="x", pady=(0, 10))

# 시간 설정 프레임
time_frame = tk.LabelFrame(main_frame, text="시간 설정", padx=10, pady=10)
time_frame.pack(fill="x", pady=(0, 10))

# 시작 시간
tk.Label(time_frame, text="시작 시간 (초 또는 mm:ss):").grid(row=0, column=0, sticky="w")
entry_start_time = tk.Entry(time_frame, width=15)
entry_start_time.grid(row=0, column=1, padx=(10, 0))
entry_start_time.insert(0, "0")

# 종료 시간
tk.Label(time_frame, text="종료 시간 (빈칸=끝까지):").grid(row=1, column=0, sticky="w")
entry_end_time = tk.Entry(time_frame, width=15)
entry_end_time.grid(row=1, column=1, padx=(10, 0))

# 영역 설정 프레임
area_frame = tk.LabelFrame(main_frame, text="추출 영역 설정 (%)", padx=10, pady=10)
area_frame.pack(fill="x", pady=(0, 10))

# X 영역
tk.Label(area_frame, text="X 시작 %:").grid(row=0, column=0, sticky="w")
entry_xstart = tk.Entry(area_frame, width=10)
entry_xstart.grid(row=0, column=1, padx=(10, 20))
entry_xstart.insert(0, "0")

tk.Label(area_frame, text="X 끝 %:").grid(row=0, column=2, sticky="w")
entry_xend = tk.Entry(area_frame, width=10)
entry_xend.grid(row=0, column=3, padx=(10, 0))
entry_xend.insert(0, "100")

# Y 영역
tk.Label(area_frame, text="Y 시작 %:").grid(row=1, column=0, sticky="w")
entry_ystart = tk.Entry(area_frame, width=10)
entry_ystart.grid(row=1, column=1, padx=(10, 20))
entry_ystart.insert(0, "70")

tk.Label(area_frame, text="Y 끝 %:").grid(row=1, column=2, sticky="w")
entry_yend = tk.Entry(area_frame, width=10)
entry_yend.grid(row=1, column=3, padx=(10, 0))
entry_yend.insert(0, "100")

# 고급 설정 프레임
advanced_frame = tk.LabelFrame(main_frame, text="고급 설정", padx=10, pady=10)
advanced_frame.pack(fill="x", pady=(0, 10))

# 임계값
tk.Label(advanced_frame, text="프레임 차이 임계값:").grid(row=0, column=0, sticky="w")
entry_threshold = tk.Entry(advanced_frame, width=15)
entry_threshold.grid(row=0, column=1, padx=(10, 0))
entry_threshold.insert(0, "5.0")

# 전환 안정화 시간
tk.Label(advanced_frame, text="전환 안정화 시간(초):").grid(row=1, column=0, sticky="w")
entry_transition = tk.Entry(advanced_frame, width=15)
entry_transition.grid(row=1, column=1, padx=(10, 0))
entry_transition.insert(0, "2.0")

# 출력 폴더명
tk.Label(advanced_frame, text="출력 폴더 접두어:").grid(row=2, column=0, sticky="w")
entry_base_folder = tk.Entry(advanced_frame, width=15)
entry_base_folder.grid(row=2, column=1, padx=(10, 0))
entry_base_folder.insert(0, "music_file_")

# 버튼 프레임
button_frame = tk.Frame(main_frame)
button_frame.pack(fill="x", pady=(20, 0))

# 설정 저장 버튼
save_button = tk.Button(button_frame, text="설정 저장", command=save_env, 
                       bg="#4CAF50", fg="white", font=("Arial", 12, "bold"),
                       height=2)
save_button.pack(side="left", fill="x", expand=True, padx=(0, 10))

# 실행 버튼
run_button = tk.Button(button_frame, text="실행", command=run_v3,
                      bg="#2196F3", fg="white", font=("Arial", 12, "bold"),
                      height=2)
run_button.pack(side="right", fill="x", expand=True, padx=(10, 0))

# 도움말
help_text = """
사용법:
1. YouTube URL 입력
2. 필요시 시간 구간 및 추출 영역 조정
3. '설정 저장' 버튼 클릭
4. '실행' 버튼 클릭하여 처리 시작

※ v3는 악보 전환을 자동 감지하여 깔끔한 결과를 제공합니다.
"""

help_label = tk.Label(main_frame, text=help_text, justify="left", 
                     font=("Arial", 9), fg="gray")
help_label.pack(pady=(20, 0))

root.mainloop()
