# 图纸管理系统 (Blueprint Management System)

**版本：** V1.0
**状态：** 功能开发完成，测试优化阶段
**更新日期：** 2026-04-11

---

## 项目简介

建立**分类分级**的图纸全生命周期管理体系，实现**保密有级、版本可溯**的企业内部图纸管理系统。

### 核心功能

| 功能 | 说明 |
|------|------|
| 📁 **图纸管理** | 创建、上传、版本控制、关联关系、CSV导出 |
| 🔐 **保密分级** | A/B/C 三级保密，两级审核流程 |
| 👥 **项目组管理** | 项目团队、成员角色、负责人权限隔离 |
| 📊 **统计看板** | 图纸总量、等级分布、更新趋势 |
| 📈 **工作量统计** | 用户贡献量化考核（创建/上传/审核数） |
| 👥 **用户管理** | 8种角色、19个权限键动态配置 |
| 📝 **系统日志** | 操作审计、行为追溯 |

---

## 技术架构

```
┌─────────────┐
│  Vue3       │  ← 前端 (Port 3000)
│  Element+   │
└──────┬──────┘
       │ REST API
┌──────▼──────┐
│  FastAPI    │  ← 后端 (Port 8000)
│  SQLAlchemy │
└──────┬──────┘
       │
┌──────▼──────┐  ┌─────────────┐
│ SQLite/PG   │  │ 文件存储     │
│   数据库     │  │ /data/drawings│
└─────────────┘  └─────────────┘
```

### 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 前端 | Vue3 + Element Plus + Pinia | 组件化开发、状态管理 |
| 后端 | Python FastAPI + SQLAlchemy | 异步高性能 |
| 数据库 | SQLite (开发) / PostgreSQL (生产) | 结构化数据 |
| 文件存储 | 本地磁盘 | 大文件支持（500MB） |
| 认证 | JWT + 动态权限 | Token + RBAC |

---

## 目录结构

```
Blueprint Management System Project/
├── frontend/              # 前端项目
│   ├── src/
│   │   ├── views/        # 16个页面组件
│   │   ├── components/   # 通用组件（MainLayout等）
│   │   ├── router/       # 路由配置 + 权限守卫
│   │   ├── stores/       # Pinia状态管理（user store）
│   │   └── utils/       # API封装
│   └── package.json
│
├── backend/               # 后端项目
│   ├── app/
│   │   ├── api/          # API路由（12个模块）
│   │   ├── models/       # SQLAlchemy模型
│   │   ├── schemas/      # Pydantic Schema
│   │   ├── core/         # 核心配置（permissions.py等）
│   │   └── main.py       # 应用入口
│   └── requirements.txt
│
└── *.md                   # 项目文档
```

---

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.10+

### 1. 启动前端

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:3000
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python init_db.py    # 初始化数据库
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
# API 文档 http://localhost:8000/docs
```

---

## 默认账户

| 用户名 | 密码 | 角色 | 权限说明 |
|--------|------|------|----------|
| admin | admin123 | 管理员 | 全部功能 |
| cto | cto123 | CTO | 查看所有图纸、看板、日志 |
| lisi_eng | 123456 | 工程师 | 创建/上传图纸、仅看自己图纸 |
| zhangsan | 123456 | 设计师 | 创建/上传图纸、仅看自己图纸 |
| lishen | 123456 | 审定人 | 保密审核、查看所有图纸 |
| wang_guest | 123456 | 访客 | 无图纸访问权限 |

---

## 核心功能

### 1. 图纸管理
- 自动编号：`{product_code}-{sequence:4digits}`
- 版本迭代：V1.0 → V1.1 → V2.0
- 技术参数：用途、材料、尺寸、保密要点
- 关联图纸：上下游关系

### 2. 保密分级审核

| 等级 | 名称 | 定义 |
|------|------|------|
| A | 核心机密 | 核心技术、核心部件 |
| B | 重要 | 重要功能部件 |
| C | 一般 | 标准件、通用件 |

**两级审核：** 创建者初定 → 审定人终审

### 3. 项目组管理
- 项目团队创建、成员管理
- 负责人/工程师角色区分
- 负责人可查看组内所有图纸

### 4. 动态权限系统
- **8种角色**：管理员、CTO、项目负责人、工程师、设计师、审定人、档案管理员、访客
- **19个权限键**：可动态配置，实时生效

---

## 核心 API

### 认证
```
POST /api/auth/login      # 登录
GET  /api/auth/me         # 获取当前用户（含权限）
POST /api/auth/logout     # 登出
```

### 图纸管理
```
GET    /api/drawings                    # 图纸列表（分页/筛选）
POST   /api/drawings                    # 创建图纸
GET    /api/drawings/{id}               # 图纸详情
PUT    /api/drawings/{id}               # 更新图纸
DELETE /api/drawings/{id}               # 删除图纸
POST   /api/drawings/{id}/versions      # 上传版本
GET    /api/drawings/{id}/versions      # 版本历史
GET    /api/drawings/export/csv         # CSV导出
```

### 保密审核
```
GET    /api/reviews/pending             # 待审核列表
POST   /api/reviews/{id}/approve        # 审核通过
POST   /api/reviews/{id}/reject         # 审核驳回
GET    /api/reviews/history/all         # 审核历史
```

### 系统管理
```
CRUD   /api/users|roles|departments|products|core-parts
GET    /api/project-groups              # 项目组管理
POST   /api/project-groups/{id}/members # 添加成员
DELETE /api/project-groups/{id}/members/{userId} # 移除成员
GET    /api/logs                       # 系统日志
GET    /api/dashboard/stats             # 统计看板
GET    /api/workload/stats             # 工作量统计
```

完整 API 文档：http://localhost:8000/docs

---

## 权限系统

### 角色定义（8种）

| 角色编码 | 角色名称 | 核心权限 |
|----------|----------|----------|
| `admin` | 管理员 | 全功能访问 |
| `cto` | CTO | 查看所有图纸、看板、日志 |
| `project_manager` | 项目负责人 | 查看项目图纸、管理产品、工作量统计 |
| `engineer` | 工程师 | 创建/上传图纸、仅看自己图纸 |
| `designer` | 设计师 | 创建/上传图纸、仅看自己图纸 |
| `reviewer` | 审定人 | 保密审核、查看所有图纸 |
| `archive_manager` | 档案管理员 | 查看/下载所有图纸、日志 |
| `guest` | 访客 | 无图纸访问权限 |

### 19个权限键

```
图纸查看: viewDashboard, viewDrawings, viewAllDrawings, viewProjectDrawings,
          viewOwnDrawings, viewPendingReview, viewAlevelDrawings
图纸操作: createDrawing, uploadVersion, downloadDrawing
保密审核: reviewConfidentiality
管理功能: manageUsers, manageRoles, manageProjectGroups, manageDepartments,
          manageProducts, manageCoreParts, viewLogs, workLog
```

---

## 开发进度

### 第一阶段：前端原型 ✅
### 第二阶段：后端开发 ✅
### 第三阶段：联调测试 ✅
### 第四阶段：测试优化 🔄 （进行中）
- [x] 权限系统重构（统一键名、动态配置）
- [x] 路由守卫
- [x] 项目组管理
- [ ] 端到端测试
- [ ] 性能优化

### 第五阶段：部署上线 📋

---

## 相关文档

- [项目文档](项目文档.md) - 详细技术文档
- [使用说明](使用说明.md) - 用户操作手册
- [需求规格说明书](图纸管理系统需求规格说明书.md)

---

## 联系方式

**开发团队：** 内部自研团队
**最后更新：** 2026-04-11
