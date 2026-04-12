# 图纸管理系统 - 前端原型

基于 **Vue3 + Element Plus** 的图纸管理系统前端原型。

## 项目结构

```
frontend/
├── index.html                 # 入口 HTML
├── package.json               # 项目依赖
├── vite.config.js            # Vite 配置
├── src/
│   ├── main.js               # 应用入口
│   ├── App.vue               # 根组件
│   ├── router/
│   │   └── index.js          # 路由配置
│   ├── components/
│   │   └── MainLayout.vue    # 主布局（侧边栏 + 顶栏）
│   └── views/
│       ├── Login.vue         # 登录页
│       ├── Dashboard.vue     # 统计看板
│       ├── DrawingsList.vue  # 图纸列表
│       ├── DrawingsCreate.vue # 新建图纸
│       ├── DrawingsDetail.vue # 图纸详情
│       ├── DrawingsUpload.vue # 上传版本
│       ├── VersionHistory.vue # 版本历史
│       ├── ReviewPage.vue    # 保密审核
│       ├── CorePartsManage.vue # 核心部件词库
│       └── ProductsManage.vue  # 产品/项目字典
```

## 功能模块

### 一期核心功能

| 页面 | 路由 | 功能说明 |
|------|------|----------|
| 登录页 | `/login` | 用户登录 |
| 统计看板 | `/dashboard` | 图纸总量、保密等级分布、版本更新趋势 |
| 图纸列表 | `/drawings` | 图纸查询、筛选、分页 |
| 新建图纸 | `/drawings/create` | 创建图纸、保密等级初定 |
| 图纸详情 | `/drawings/:id` | 查看详细信息、技术参数、关联图纸 |
| 上传版本 | `/drawings/:id/upload` | 上传新版本、填写变更说明 |
| 版本历史 | `/drawings/:id/history` | 查看历史版本、版本对比 |
| 保密审核 | `/review` | 审定人审核保密等级（两级审核） |
| 词库管理 | `/core-parts` | 核心部件关键词管理 |
| 产品字典 | `/products` | 产品/项目字典管理 |

## 快速启动

```bash
# 进入项目目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev

# 构建生产版本
npm run build
```

## 技术栈

- **框架**: Vue 3.4+
- **UI 库**: Element Plus 2.5+
- **路由**: Vue Router 4.2+
- **构建工具**: Vite 5.0+
- **图标**: @element-plus/icons-vue

## 页面预览说明

本原型为静态页面演示，数据均为模拟数据。主要展示：
- 页面布局和交互设计
- 表单字段和验证规则
- 数据表格和筛选功能
- 保密等级两级审核流程
- 版本管理和对比功能

## 与需求文档对应关系

本原型严格对应《图纸管理系统需求规格说明书》一期功能：
- 【F1】图纸基础管理 → DrawingsList, DrawingsCreate, DrawingsDetail
- 【F2】保密等级认定 → ReviewPage, DrawingsCreate
- 【F3】版本管理 → DrawingsUpload, VersionHistory
- 【F5】技术参数标注 → DrawingsDetail
- 【F6】基础检索 → DrawingsList
- 【F7】关联图纸管理 → DrawingsDetail
- 【F8】统计看板 → Dashboard
- 系统管理 → CorePartsManage, ProductsManage
