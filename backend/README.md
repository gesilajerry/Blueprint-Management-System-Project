# 图纸管理系统 - 后端服务

基于 **FastAPI + SQLAlchemy + PostgreSQL** 的后端服务。

## 项目结构

```
backend/
├── app/
│   ├── api/                    # API 路由
│   │   ├── deps.py             # 依赖注入
│   │   ├── auth.py             # 认证接口
│   │   ├── users.py            # 用户管理
│   │   ├── drawings.py         # 图纸管理
│   │   ├── departments.py      # 部门管理
│   │   ├── products.py         # 产品管理
│   │   ├── reviews.py          # 保密审核
│   │   └── logs.py             # 系统日志
│   ├── core/                   # 核心模块
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库连接
│   │   ├── security.py         # 安全工具（JWT/密码）
│   │   └── logger.py           # 日志记录
│   ├── models/                 # SQLAlchemy 模型
│   │   ├── user.py
│   │   ├── role.py
│   │   ├── department.py
│   │   ├── product.py
│   │   ├── drawing.py
│   │   ├── core_part.py
│   │   └── system_log.py
│   ├── schemas/                # Pydantic Schema
│   │   └── __init__.py
│   └── main.py                 # 应用入口
├── logs/                       # 日志目录
├── init_db.py                  # 初始化脚本
├── requirements.txt            # 依赖列表
└── .env.example                # 环境变量示例
```

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接等
```

### 3. 初始化数据库

```bash
# 确保 PostgreSQL 已启动并创建了 blueprint_db 数据库
python init_db.py
```

### 4. 启动服务

```bash
# 开发模式
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 生产模式
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API 文档

启动服务后访问：
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 端点

### 认证接口
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| POST | `/api/auth/logout` | 用户登出 |

### 用户管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 用户列表 |
| POST | `/api/users` | 创建用户 |
| GET | `/api/users/{id}` | 用户详情 |
| PUT | `/api/users/{id}` | 更新用户 |
| DELETE | `/api/users/{id}` | 删除用户 |

### 图纸管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/drawings` | 图纸列表 |
| POST | `/api/drawings` | 创建图纸 |
| GET | `/api/drawings/{id}` | 图纸详情 |
| PUT | `/api/drawings/{id}` | 更新图纸 |
| DELETE | `/api/drawings/{id}` | 作废图纸 |
| POST | `/api/drawings/{id}/versions` | 上传版本 |
| GET | `/api/drawings/{id}/versions` | 版本历史 |

### 部门管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/departments` | 部门列表 |
| POST | `/api/departments` | 创建部门 |
| PUT | `/api/departments/{id}` | 更新部门 |
| DELETE | `/api/departments/{id}` | 删除部门 |

### 产品管理
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/products` | 产品列表 |
| POST | `/api/products` | 创建产品 |
| PUT | `/api/products/{id}` | 更新产品 |
| DELETE | `/api/products/{id}` | 归档产品 |

### 保密审核
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/reviews/pending` | 待审核列表 |
| POST | `/api/reviews/{id}/approve` | 审核通过 |
| POST | `/api/reviews/{id}/reject` | 审核驳回 |

### 系统日志
| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/logs` | 日志列表（可筛选） |

## 默认用户

初始化后创建以下测试用户：

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| zhangsan | 123456 | 设计师 |
| lishen | 123456 | 审定人 |

## 日志记录

系统自动记录以下操作：
- 用户登录/登出
- 图纸创建/更新/删除
- 版本上传
- 保密等级审核
- 系统配置变更

日志文件位置：`logs/app.log`
日志查询 API：`GET /api/logs`

## 技术栈

- **框架**: FastAPI 0.109
- **ORM**: SQLAlchemy 2.0
- **数据库**: PostgreSQL
- **认证**: JWT (python-jose)
- **密码**: bcrypt (passlib)
- **验证**: Pydantic 2.5
- **日志**: Python logging (轮转文件)

## Docker 部署

```bash
# 构建镜像
docker build -t blueprint-backend .

# 运行容器
docker run -d \
  --name blueprint-backend \
  -p 8000:8000 \
  -v /data/drawings:/data/drawings \
  --env-file .env \
  blueprint-backend
```
