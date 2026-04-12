#!/usr/bin/env python
"""
初始化数据库脚本
创建默认数据和测试用户
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.core.security import get_password_hash
from app.models import User, Role, Department
from app.models.core_part import CorePartKeyword
from app.models.work_log import WorkLog


def init_db():
    """初始化数据库"""
    # 创建表
    from app.core.database import Base
    Base.metadata.create_all(bind=engine)
    print("✓ 数据表已创建")

    db = SessionLocal()

    try:
        # 创建默认角色
        roles = [
            {"id": "role_admin", "name": "管理员", "code": "admin"},
            {"id": "role_cto", "name": "CTO", "code": "cto"},
            {"id": "role_project_manager", "name": "项目经理", "code": "project_manager"},
            {"id": "role_engineer", "name": "工程师", "code": "engineer"},
            {"id": "role_designer", "name": "设计师", "code": "designer"},
            {"id": "role_reviewer", "name": "审定人", "code": "reviewer"},
            {"id": "role_guest", "name": "访客", "code": "guest"},
            {"id": "role_observer", "name": "观察员", "code": "observer"},
        ]

        for role_data in roles:
            role = db.query(Role).filter(Role.code == role_data["code"]).first()
            if not role:
                role = Role(**role_data)
                db.add(role)
                print(f"✓ 创建角色：{role_data['name']}")

        # 创建默认部门（已不再使用，保留数据库兼容）
        departments = [
            {"id": "dept_rd1", "name": "研发工程部", "code": "RD01", "manager": "张总"},
        ]

        for dept_data in departments:
            dept = db.query(Department).filter(Department.code == dept_data["code"]).first()
            if not dept:
                dept = Department(**dept_data)
                db.add(dept)
                print(f"✓ 创建部门：{dept_data['name']}")

        db.commit()

        # 创建默认用户
        users = [
            {
                "username": "admin",
                "name": "系统管理员",
                "password_hash": get_password_hash("admin123"),
                "department_id": "dept_rd1",
                "role_id": "role_admin",
                "email": "admin@company.com"
            },
            {
                "username": "cto",
                "name": "王 CTO",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_cto",
                "email": "cto@company.com"
            },
            {
                "username": "zhang",
                "name": "张经理",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_project_manager",
                "email": "zhang@company.com"
            },
            {
                "username": "lisi",
                "name": "李工程师",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_engineer",
                "email": "lisi@company.com"
            },
            {
                "username": "zhangsan",
                "name": "张三",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_designer",
                "email": "zhangsan@company.com"
            },
            {
                "username": "lishen",
                "name": "李审定",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_reviewer",
                "email": "lishen@company.com"
            },
            {
                "username": "archivemgr",
                "name": "档案管理员",
                "password_hash": get_password_hash("123456"),
                "department_id": "dept_rd1",
                "role_id": "role_archive_manager",
                "email": "archive@company.com"
            }
        ]

        for user_data in users:
            user = db.query(User).filter(User.username == user_data["username"]).first()
            if not user:
                user = User(**user_data)
                db.add(user)
                print(f"✓ 创建用户：{user_data['username']} (密码：123456)")

        db.commit()

        # 创建核心部件词库初始数据
        keywords = ["电机", "控制系统", "传动机构", "核心模块", "专用机构", "传感系统", "驱动系统", "精密结构"]
        for kw in keywords:
            existing = db.query(CorePartKeyword).filter(CorePartKeyword.keyword == kw).first()
            if not existing:
                keyword = CorePartKeyword(keyword=kw)
                db.add(keyword)
                print(f"✓ 添加关键词：{kw}")

        db.commit()
        print("\n✓ 数据库初始化完成!")
        print("\n默认用户:")
        print("  admin / admin123  (管理员)")
        print("  zhangsan / 123456 (设计师)")
        print("  lishen / 123456   (审定人)")

    except Exception as e:
        db.rollback()
        print(f"✗ 初始化失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
