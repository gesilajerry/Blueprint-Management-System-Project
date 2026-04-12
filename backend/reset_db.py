#!/usr/bin/env python
"""
完整重置数据库脚本
按照当前数据库结构，重置所有测试数据
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal, Base
from app.core.security import get_password_hash
from app.models import User, Role, Department
from app.models.core_part import CorePartKeyword
from app.models.work_log import WorkLog


def reset_database():
    """重置数据库"""
    print("=" * 50)
    print("开始重置数据库...")
    print("=" * 50)

    # 删除旧数据库文件
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "blueprint_dev.db")
    if os.path.exists(db_path):
        os.remove(db_path)
        print(f"✓ 已删除旧数据库: {db_path}")

    # 重新创建所有表
    Base.metadata.create_all(bind=engine)
    print("✓ 数据表已创建")

    db = SessionLocal()

    try:
        # ==================== 角色数据 ====================
        print("\n--- 初始化角色 ---")
        roles = [
            {"id": "role_admin", "name": "管理员", "code": "admin"},
            {"id": "role_cto", "name": "CTO", "code": "cto"},
            {"id": "role_project_manager", "name": "项目经理", "code": "project_manager"},
            {"id": "role_engineer", "name": "工程师", "code": "engineer"},
            {"id": "role_designer", "name": "设计师", "code": "designer"},
            {"id": "role_reviewer", "name": "审定人", "code": "reviewer"},
            {"id": "role_guest", "name": "访客", "code": "guest"},
        ]

        for role_data in roles:
            role = Role(**role_data)
            db.add(role)
            print(f"✓ 角色: {role_data['name']} ({role_data['code']})")

        # ==================== 部门数据 ====================
        print("\n--- 初始化部门 ---")
        departments = [
            {"id": "dept_rd1", "name": "研发工程部", "code": "RD01", "manager": "张总"},
        ]

        for dept_data in departments:
            dept = Department(**dept_data)
            db.add(dept)
            print(f"✓ 部门: {dept_data['name']} ({dept_data['code']})")

        db.commit()

        # ==================== 用户数据 ====================
        print("\n--- 初始化用户 ---")
        users = [
            {
                "username": "admin",
                "name": "系统管理员",
                "password_hash": get_password_hash("admin123"),
                "department_id": "dept_rd1",
                "role_id": "role_admin",
                "email": "admin@company.com",
                "phone": "13800000001"
            },
            {
                "username": "cto",
                "name": "王 CTO",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_cto",
                "email": "cto@company.com",
                "phone": "13800000002"
            },
            {
                "username": "zhang_pm",
                "name": "张项目经理",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_project_manager",
                "email": "zhang_pm@company.com",
                "phone": "13800000003"
            },
            {
                "username": "lisi_eng",
                "name": "李工程师",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_engineer",
                "email": "lisi_eng@company.com",
                "phone": "13800000004"
            },
            {
                "username": "zhangsan",
                "name": "张三设计师",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_designer",
                "email": "zhangsan@company.com",
                "phone": "13800000005"
            },
            {
                "username": "lishen",
                "name": "李审定",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_reviewer",
                "email": "lishen@company.com",
                "phone": "13800000006"
            },
            {
                "username": "wang_guest",
                "name": "王访客",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_guest",
                "email": "wang_guest@company.com",
                "phone": "13800000007"
            },
        ]

        for user_data in users:
            user = User(**user_data)
            db.add(user)
            print(f"✓ 用户: {user_data['username']} ({user_data['name']}, 密码: 123456)")

        # ==================== 核心部件词库 ====================
        print("\n--- 初始化核心部件词库 ---")
        keywords = [
            "电机", "控制系统", "传动机构", "核心模块", "专用机构",
            "传感系统", "驱动系统", "精密结构", "电源模块", "通信模块"
        ]

        for kw in keywords:
            keyword = CorePartKeyword(keyword=kw)
            db.add(keyword)
            print(f"✓ 关键词: {kw}")

        db.commit()

        print("\n" + "=" * 50)
        print("✓ 数据库重置完成!")
        print("=" * 50)
        print("\n默认用户:")
        print("  admin / admin123  (管理员)")
        print("  cto / 123456      (CTO)")
        print("  zhang_pm / 123456 (项目经理)")
        print("  lisi_eng / 123456 (工程师)")
        print("  zhangsan / 123456 (设计师)")
        print("  lishen / 123456   (审定人)")
        print("  wang_guest / 123456 (访客)")
        print("\n角色列表:")
        print("  1. 管理员 (admin)")
        print("  2. CTO (cto)")
        print("  3. 项目经理 (project_manager)")
        print("  4. 工程师 (engineer)")
        print("  5. 设计师 (designer)")
        print("  6. 审定人 (reviewer)")
        print("  7. 访客 (guest)")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 重置失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_database()
