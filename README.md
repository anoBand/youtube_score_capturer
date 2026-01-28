# YouTube Score Capturer

## 소개
YouTube 영상에서 악보를 자동으로 캡처하여 PDF로 만들어주는 도구임

## 주요 기능
- **영상 처리**: yt-dlp로 YouTube 영상을 다운로드하거나 스트리밍하여 분석함
- **프레임 캡처**: OpenCV를 이용해 설정된 구간, 좌표의 악보 영역만 정밀하게 캡처함
- **중복 방지**: 이전 프레임과 비교하여 변화가 있는 경우에만 저장하여 중복을 최소화함
- **PDF 변환**: 캡처된 이미지들을 A4 크기에 맞춰 자동으로 배치하고 하나의 PDF 파일로 생성함
- **웹 UI 제공**: Flask 기반 웹 인터페이스를 통해 직관적인 조작과 실시간 미리보기를 지원함

## Installation and Running (Local Development)
This section guides you through setting up and running the application locally for development purposes.

1.  **Install dependencies**: `pip install -r requirements.txt`
2.  **Run the application**: `python app.py`
3.  **Access the web interface**: Open your web browser and navigate to `http://localhost:5000`

## Deployment
This project has been successfully deployed to a web server. For production deployment of Flask applications, it is recommended to use a WSGI server like Gunicorn or uWSGI, and a reverse proxy like Nginx or Apache.

**Example Deployment Steps (using Gunicorn and Nginx):**

1.  **Prepare your environment**:
    *   Install necessary system dependencies.
    *   Set up a virtual environment and install project dependencies: `pip install -r requirements.txt gunicorn`
2.  **Run Gunicorn**:
    *   Start Gunicorn to serve the Flask application: `gunicorn -w 4 'app:app'` (replace `app:app` with your application's entry point if different).
3.  **Configure Nginx**:
    *   Set up Nginx as a reverse proxy to forward requests to Gunicorn. An example Nginx configuration might look like this:
        ```nginx
        server {
            listen 80;
            server_name your_domain.com; # Replace with your domain

            location / {
                proxy_pass http://127.0.0.1:8000; # Gunicorn default port
                proxy_set_header Host $host;
                proxy_set_header X-Real-IP $remote_addr;
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header X-Forwarded-Proto $scheme;
            }
        }
        ```
    *   Reload Nginx to apply changes.
4.  **Process Management**:
    *   Use a process manager like `systemd` or `Supervisor` to ensure Gunicorn runs continuously and restarts automatically.

**Note**: Specific deployment steps can vary greatly depending on your server environment and chosen deployment platform (e.g., Docker, Heroku, AWS, Google Cloud). Refer to the documentation for your chosen platform for detailed instructions.



## 기술 스택
- **Language**: Python
- **Web**: Flask
- **Media**: OpenCV, yt-dlp, Pillow, FPDF
