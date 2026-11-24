
# CampusFlow

## Hệ thống quản lý học tập và điểm danh thông minh

CampusFlow là phần mềm quản lý học tập được xây dựng bằng Python
và Django, hướng đến các trường học, trung tâm đào tạo và lớp học.

## 1. Công nghệ

- Python 3.12+
- Django 5.2 LTS
- Django REST Framework
- SQLite
- PostgreSQL
- Bootstrap 5
- Pytest

## 2. Yêu cầu môi trường

- Python 3.12 hoặc 3.13
- Git
- Visual Studio Code
- Windows 10/11 hoặc hệ điều hành tương thích

## 3. Cài đặt

Clone repository:

```bash
git clone YOUR_REPOSITORY_URL
cd CampusFlow
```

Tạo môi trường ảo:

```bash
python -m venv .venv
```

Kích hoạt trên Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Cài dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements/development.txt
```

Tạo file môi trường:

```powershell
Copy-Item .env.example .env
```

Cấu hình SECRET_KEY trong file .env.

## 4. Khởi tạo database

Tạo migration:

```bash
python manage.py makemigrations accounts
```

Áp dụng migration:

```bash
python manage.py migrate
```

## 5. Tạo tài khoản quản trị

```bash
python manage.py createsuperuser
```

## 6. Chạy ứng dụng

```bash
python manage.py runserver
```

Truy cập:

- Ứng dụng: http://127.0.0.1:8000/
- Django Admin: http://127.0.0.1:8000/admin/
- Health Check: http://127.0.0.1:8000/health/

## 7. Kiểm thử

```bash
python manage.py check
pytest
ruff check .
```

## 8. Cấu trúc

- apps/: các ứng dụng nghiệp vụ.
- config/: cấu hình dự án.
- requirements/: dependencies.
- static/: tài nguyên giao diện.
- templates/: giao diện HTML.
- docs/: tài liệu kỹ thuật.
- tests/: kiểm thử tổng thể.

## 9. Nguyên tắc phát triển

- Ưu tiên bảo mật.
- Phân quyền rõ ràng.
- Kiểm thử trước khi phát hành.
- Không lưu thông tin bí mật trong Git.
- Không đưa dữ liệu cá nhân thật vào dữ liệu demo.
- Giao diện và tài liệu hướng tới người dùng Việt Nam.

## 10. Trạng thái

Phiên bản: 0.1.0

Giai đoạn: Project Foundation
