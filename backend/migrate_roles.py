#!/usr/bin/env python
"""
数据库迁移脚本
更新角色数据：移除部门负责人，添加项目经理和工程师
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.core.database import engine, SessionLocal
from app.models import User, Role


def migrate_roles():
    """迁移角色数据"""
    db = SessionLocal()

    try:
        print("开始数据库角色迁移...")

        # 1. 删除部门负责人角色（如果存在）
        dept_head = db.query(Role).filter(Role.code == "dept_head").first()
        if dept_head:
            # 更新使用该角色的用户
            users_with_dept_head = db.query(User).filter(User.role_id == dept_head.id).all()
            if users_with_dept_head:
                print(f"发现 {len(users_with_dept_head)} 个用户使用部门负责人角色")

            db.delete(dept_head)
            print("✓ 删除部门负责人角色")

        # 2. 添加项目经理角色（如果不存在）
        pm_role = db.query(Role).filter(Role.code == "project_manager").first()
        if not pm_role:
            pm_role = Role(
                id="role_project_manager",
                name="项目经理",
                code="project_manager"
            )
            db.add(pm_role)
            print("✓ 添加项目经理角色")

        # 3. 添加工程师角色（如果不存在）
        engineer_role = db.query(Role).filter(Role.code == "engineer").first()
        if not engineer_role:
            engineer_role = Role(
                id="role_engineer",
                name="工程师",
                code="engineer"
            )
            db.add(engineer_role)
            print("✓ 添加工程师角色")

        db.commit()
        print("\n✓ 数据库角色迁移完成!")

    except Exception as e:
        db.rollback()
        print(f"✗ 迁移失败：{e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    migrate_roles()
