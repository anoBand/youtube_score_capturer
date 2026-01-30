# 가장 가벼운 Nginx 이미지를 베이스로 사용
FROM nginx:alpine

# 기본 Nginx 설정 파일 삭제 (필요 시 커스텀 설정을 위해)
# RUN rm /etc/nginx/conf.d/default.conf

# 현재 폴더의 index.html을 Nginx의 기본 웹 루트 폴더로 복사
COPY index.html /usr/share/nginx/html/index.html

# (선택 사항) 이미지 등 추가 정적 리소스가 있다면 폴더째 복사
# COPY static/ /usr/share/nginx/html/static/

# Nginx의 기본 포트인 80번 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]