import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
from PIL import Image, ImageTk

# 실행 시 기준 경로를 올바르게 설정하는 함수
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def generate_env_py(
    url: str,
    start_time_raw: str,
    end_time_raw: str,
    threshold_diff: float,
    tab_region_ratio: float,
    x_start_percent_raw: float,
    x_end_percent_raw: float,
    y_start_percent_raw: float,
    y_end_percent_raw: float,
    transition_stable_sec: float,
    base_folder_name: str
):
    """env.py를 생성(또는 갱신)해주는 함수 (src 폴더 내부에 생성)"""
    if getattr(sys, 'frozen', False):
    #test.exe로 실행한 경우,test.exe를 보관한 디렉토리의 full path를 취득
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        #python test.py로 실행한 경우,test.py를 보관한 디렉토리의 full path를 취득
        base_dir = os.path.dirname(os.path.abspath(__file__))
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

# v1 전용 변수: 영상 하단 몇 %를 추출할 지 결정
TAB_REGION_RATIO: float = {tab_region_ratio}

# 잘라낼 영역 퍼센트(0% ~ 100%) RAW에서 입력
X_START_PERCENT_RAW: float = {x_start_percent_raw}
X_END_PERCENT_RAW: float   = {x_end_percent_raw}
Y_START_PERCENT_RAW: float = {y_start_percent_raw}
Y_END_PERCENT_RAW: float   = {y_end_percent_raw}

# v3 추가 변수: n초만큼 고정된다면 리스트에 추가
TRANSITION_STABLE_SEC: float = {transition_stable_sec}

# 출력 폴더명 접두어
BASE_FOLDER_NAME: str = "{base_folder_name}"
"""
        )

def run_selected_py():
    """선택된 파일을 CMD 창에서 실행 (exe 위치의 실제 폴더에서 실행)"""
    selected = radio_var.get()
    if not selected:
        messagebox.showerror("오류", "실행할 파일을 선택하세요!")
        return

    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)  # exe 실행 파일 위치
        python_executable = "python"
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))  # py 실행 파일 위치
        python_executable = sys.executable

    src_dir = os.path.join(base_dir, "src")  # 실제 src 폴더 경로

    # 환경변수(PATH)에 src 추가 (ffmpeg.exe 사용위해)
    new_env = dict(os.environ)
    new_env["PATH"] = src_dir + os.pathsep + new_env["PATH"]

    # subprocess 호출 시 cwd를 실제 폴더로 명시적 지정
    subprocess.Popen(
        ["cmd", "/k", python_executable, f"{selected}.exe"],
        env=new_env,
        cwd=src_dir  # ← 실제 디렉토리 명시적 지정 (중요!)
    )


def save_env():
    # 입력값 가져오기
    url = entry_url.get().strip()
    start_time = entry_start_time.get().strip()
    end_time = entry_end_time.get().strip()
    threshold = entry_threshold.get().strip()
    tab_ratio = entry_tab_ratio.get().strip()
    x_start = entry_xstart.get().strip()
    x_end = entry_xend.get().strip()
    y_start = entry_ystart.get().strip()
    y_end = entry_yend.get().strip()
    transition_sec = entry_transition.get().strip()
    base_folder = entry_base_folder.get().strip()

    try:
        # 숫자 변환 (기본값 있을 경우 처리 가능)
        threshold_val = float(threshold) if threshold else 15.0
        tab_ratio_val = float(tab_ratio) if tab_ratio else 0.45
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
        url=url or "https://youtu.be/x_NGsTIJptw?si=CzoRt-qTqrdJW3Dy",  # 혹은 기본값
        start_time_raw=start_time or "0",
        end_time_raw=end_time_val,  # None이면 None 그대로 들어감
        threshold_diff=threshold_val,
        tab_region_ratio=tab_ratio_val,
        x_start_percent_raw=x_start_val,
        x_end_percent_raw=x_end_val,
        y_start_percent_raw=y_start_val,
        y_end_percent_raw=y_end_val,
        transition_stable_sec=transition_val,
        base_folder_name=base_folder or "music_file_"
    )

    messagebox.showinfo("저장 완료", "env.py가 성공적으로 생성/갱신되었습니다!")

# 간단한 계산: (분자 / 분모) → XX.XX% 표시
def calc_ratio():
    """entry_numer, entry_denom에서 값을 가져와 % 계산"""
    try:
        numerator = float(entry_numer.get())
        denominator = float(entry_denom.get())

        if denominator == 0:
            label_calc_result.config(text="분모가 0이면 계산 불가")
            return

        ratio = (numerator / denominator) * 100.0
        # 소수점 2자리까지 출력
        label_calc_result.config(text=f"{ratio:.2f}%")
    except ValueError:
        label_calc_result.config(text="숫자만 입력하세요")

root = tk.Tk()
root.title("YT IMG EXTRACTOR")

# ──────────[1] 메인 입력 폼──────────
tk.Label(root, text="URL:").grid(row=0, column=0, sticky="w")
entry_url = tk.Entry(root, width=50)
entry_url.insert(0, "**URL을 여기에 입력하세요**")
entry_url.grid(row=0, column=1, padx=5, pady=15)

tk.Label(root, text="각 프레임 이미지 추출 민감도 (낮을수록 예민, 필요 시 수정):").grid(row=1, column=0, sticky="w")
entry_threshold = tk.Entry(root, width=50)
entry_threshold.insert(0, "15")
entry_threshold.grid(row=1, column=1, padx=5, pady=10)

tk.Label(root, text="[V2, V3] 시작 시간 (ex: 0 or 1:23):").grid(row=2, column=0, sticky="w")
entry_start_time = tk.Entry(root, width=50)
entry_start_time.insert(0, "0")
entry_start_time.grid(row=2, column=1, padx=5, pady=5)

tk.Label(root, text="[V2, V3] 종료 시간 (ex: 2:30, 미 입력시 끝까지):").grid(row=3, column=0, sticky="w")
entry_end_time = tk.Entry(root, width=50)
entry_end_time.grid(row=3, column=1, padx=5, pady=5)

tk.Label(root, text="[V1] 세로 아래부터 추출 영역:").grid(row=4, column=0, sticky="w")
entry_tab_ratio = tk.Entry(root, width=50)
entry_tab_ratio.insert(0, "0.45")
entry_tab_ratio.grid(row=4, column=1, padx=5, pady=5)

tk.Label(root, text="[V3] 평균 악보 고정 시간 (초, 필요 시 수정):").grid(row=5, column=0, sticky="w")
entry_transition = tk.Entry(root, width=50)
entry_transition.insert(0, "2.0")
entry_transition.grid(row=5, column=1, padx=5, pady=10)

tk.Label(root, text="[V2, V3] 가로 시작% (0~100):").grid(row=6, column=0, sticky="w")
entry_xstart = tk.Entry(root, width=50)
entry_xstart.insert(0, "0")
entry_xstart.grid(row=6, column=1, padx=5, pady=5)

tk.Label(root, text="[V2, V3] 가로 끝% (0~100):").grid(row=7, column=0, sticky="w")
entry_xend = tk.Entry(root, width=50)
entry_xend.insert(0, "100")
entry_xend.grid(row=7, column=1, padx=5, pady=5)

tk.Label(root, text="[V2, V3] 세로 시작% (0~100):").grid(row=8, column=0, sticky="w")
entry_ystart = tk.Entry(root, width=50)
entry_ystart.insert(0, "70")
entry_ystart.grid(row=8, column=1, padx=5, pady=5)

tk.Label(root, text="[V2, V3] 세로 끝% (0~100):").grid(row=9, column=0, sticky="w")
entry_yend = tk.Entry(root, width=50)
entry_yend.insert(0, "100")
entry_yend.grid(row=9, column=1, padx=5, pady=5)

tk.Label(root, text="[V2, V3] 기본 폴더 이름 (필요 시 수정):").grid(row=10, column=0, sticky="w")
entry_base_folder = tk.Entry(root, width=50)
entry_base_folder.insert(0, "music_file_")
entry_base_folder.grid(row=10, column=1, padx=5, pady=5)

# env.py 저장 버튼
tk.Button(root, text="(필수) env.py 저장", command=save_env).grid(row=11, column=0, columnspan=2, pady=30)

# ─────────────────────────────────────────────────────────────
# (1) 계산기 부분 (Frame)
calc_frame = tk.Frame(root, bd=1, relief="groove")
calc_frame.grid(row=12, column=0, padx=10, pady=10, sticky="nw")

tk.Label(calc_frame, text="== 간단 비율 계산 ==").grid(row=0, column=0, columnspan=2, pady=5)

tk.Label(calc_frame, text="해당 픽셀 위치:").grid(row=1, column=0, sticky="e")
entry_numer = tk.Entry(calc_frame, width=20)
entry_numer.grid(row=1, column=1, padx=5, pady=5, sticky="w")

tk.Label(calc_frame, text="전체 프레임 크기:").grid(row=2, column=0, sticky="e")
entry_denom = tk.Entry(calc_frame, width=20)
entry_denom.grid(row=2, column=1, padx=5, pady=5, sticky="w")

tk.Button(calc_frame, text="계산하기", command=calc_ratio).grid(row=3, column=0, columnspan=2, pady=15)

label_calc_result = tk.Label(calc_frame, text="결과가 여기에 표시됩니다")
label_calc_result.grid(row=4, column=0, columnspan=2, pady=5)

# ─────────────────────────────────────────────────────────────
# (2) 이미지 부분 (same row=12, but column=1)
try:
    if getattr(sys, 'frozen', False):
        #test.exe로 실행한 경우,test.exe를 보관한 디렉토리의 full path를 취득
        base_dir = os.path.dirname(os.path.abspath(sys.executable))
    else:
        #python test.py로 실행한 경우,test.py를 보관한 디렉토리의 full path를 취득
        base_dir = os.path.dirname(os.path.abspath(__file__))
    img_path = os.path.join(base_dir, "src", "guide.png")  # ← 경로 수정
    img_src = Image.open(img_path)
    scale = 0.3
    new_width = int(img_src.width * scale)
    new_height = int(img_src.height * scale)
    img_src = img_src.resize((new_width, new_height), Image.LANCZOS)
    photo = ImageTk.PhotoImage(img_src)

    img_label = tk.Label(root, image=photo)
    img_label.grid(row=12, column=1, padx=10, pady=30, sticky="nw")
    img_label.image = photo  # 참조 유지
except:
    tk.Label(root, text="이미지 로드 실패").grid(row=12, column=1, sticky="nw")
# ─────────────────────────────────────────────────────────────
# (3) 라디오버튼 & 실행 버튼 (row=13~15, 아래쪽)
# 라디오버튼 변수
radio_var = tk.StringVar()

# 라디오버튼들을 담을 frame 생성
radio_frame = tk.Frame(root)
radio_frame.grid(row=13, column=0, columnspan=2, pady=10)

# 라벨
tk.Label(radio_frame, text="실행할 파일 선택:").pack(side="left", padx=(0, 10))

# 라디오버튼들
tk.Radiobutton(radio_frame, text="Ver.1", variable=radio_var, value="TAB_maker_v1").pack(side="left", padx=5)
tk.Radiobutton(radio_frame, text="Ver.2", variable=radio_var, value="TAB_maker_v2").pack(side="left", padx=5)
tk.Radiobutton(radio_frame, text="Ver.3", variable=radio_var, value="TAB_maker_v3").pack(side="left", padx=5)

tk.Button(root, text="(필수) 선택된 파일 실행", command=run_selected_py).grid(row=14, column=0, columnspan=2, pady=10)

root.mainloop()
