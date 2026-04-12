# 测试计划

## 一、单元测试

### 1. 认证模块测试

```python
# tests/test_auth.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_login_success():
    """测试登录成功"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert "access_token" in data["data"]

def test_login_wrong_password():
    """测试密码错误"""
    response = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "wrong"
    })
    assert response.status_code == 401

def test_get_me():
    """测试获取当前用户"""
    # 先登录获取 token
    login_resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = login_resp.json()["data"]["access_token"]

    # 携带 token 访问
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/auth/me", headers=headers)
    assert response.status_code == 200
```

### 2. 图纸管理测试

```python
# tests/test_drawings.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def get_auth_headers():
    """获取认证头"""
    resp = client.post("/api/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_drawing():
    """测试创建图纸"""
    headers = get_auth_headers()
    response = client.post("/api/drawings", headers=headers, json={
        "name": "测试图纸",
        "product_id": "product-001",
        "department_id": "dept-001",
        "confidentiality_level": "B",
        "is_core_part": False
    })
    assert response.status_code == 200

def test_get_drawings_list():
    """测试获取图纸列表"""
    headers = get_auth_headers()
    response = client.get("/api/drawings?page=1&size=10", headers=headers)
    assert response.status_code == 200
    assert "items" in response.json()["data"]

def test_upload_version():
    """测试上传版本"""
    headers = get_auth_headers()
    # 准备测试文件
    files = {"file": ("test.dwg", b"binary content")}
    data = {
        "change_types": "optimize",
        "change_reason": "性能优化"
    }
    response = client.post(
        "/api/drawings/drawing-001/versions",
        headers=headers,
        files=files,
        data=data
    )
    assert response.status_code in [200, 404]  # 404 表示图纸不存在（测试数据）
```

### 3. 用户管理测试

```python
# tests/test_users.py
def test_create_user():
    """测试创建用户"""
    headers = get_auth_headers()
    response = client.post("/api/users", headers=headers, json={
        "username": "testuser",
        "name": "测试用户",
        "password": "123456",
        "department_id": "dept-001",
        "role_id": "role-designer"
    })
    assert response.status_code in [200, 400]  # 400 表示用户已存在

def test_get_users():
    """测试获取用户列表"""
    headers = get_auth_headers()
    response = client.get("/api/users?page=1&size=10", headers=headers)
    assert response.status_code == 200
```

## 二、集成测试

### 1. 完整流程测试

```python
# tests/test_integration.py
def test_full_workflow():
    """测试完整工作流程"""
    # 1. 登录
    login_resp = client.post("/api/auth/login", json={
        "username": "zhangsan",
        "password": "123456"
    })
    assert login_resp.status_code == 200
    token = login_resp.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. 创建图纸
    create_resp = client.post("/api/drawings", headers=headers, json={
        "name": "集成测试图纸",
        "product_id": "product-001",
        "department_id": "dept-001",
        "confidentiality_level": "C",
        "is_core_part": False
    })
    assert create_resp.status_code == 200
    drawing_id = create_resp.json()["data"]["id"]

    # 3. 上传版本
    # ... (文件上传测试)

    # 4. 查看版本历史
    history_resp = client.get(f"/api/drawings/{drawing_id}/versions", headers=headers)
    assert history_resp.status_code == 200

    # 5. 查看系统日志
    logs_resp = client.get("/api/logs", headers=headers)
    assert logs_resp.status_code == 200
```

## 三、性能测试

### 使用 Locust 进行压力测试

```python
# tests/locustfile.py
from locust import HttpUser, task, between

class DrawingUser(HttpUser):
    wait_time = between(1, 5)

    @task(3)
    def get_drawings(self):
        self.client.get("/api/drawings")

    @task(2)
    def get_products(self):
        self.client.get("/api/products")

    @task(1)
    def get_logs(self):
        self.client.get("/api/logs")
```

运行压测：
```bash
locust -f tests/locustfile.py --host=http://localhost:8000
```

## 四、运行测试

```bash
# 安装测试依赖
pip install pytest httpx locust

# 运行单元测试
pytest tests/ -v

# 运行覆盖率测试
pytest tests/ -v --cov=app --cov-report=html

# 运行集成测试
pytest tests/test_integration.py -v
```

## 五、测试检查清单

### 功能测试
- [ ] 用户登录/登出
- [ ] 图纸 CRUD 操作
- [ ] 版本上传和下载
- [ ] 保密等级审核流程
- [ ] 用户/角色/部门管理
- [ ] 系统日志记录

### 安全测试
- [ ] 未认证访问拦截
- [ ] 权限控制验证
- [ ] SQL 注入防护
- [ ] XSS 防护
- [ ] 文件上传限制

### 性能测试
- [ ] 并发用户测试
- [ ] 大数据量查询
- [ ] 文件上传性能
- [ ] API 响应时间

### 兼容性测试
- [ ] Chrome 浏览器
- [ ] Firefox 浏览器
- [ ] Safari 浏览器
- [ ] Edge 浏览器
