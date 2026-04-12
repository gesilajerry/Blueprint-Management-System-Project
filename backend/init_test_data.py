#!/usr/bin/env python
"""
完整初始化测试数据脚本
包括：项目组、产品、图纸等
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from datetime import datetime, timedelta, date
from app.core.database import SessionLocal
from app.models import User, Role, Department, Product, ProjectGroup
from app.models.drawing import Drawing, DrawingVersion, ReviewStatus, ConfidentialityLevel, DrawingStatus


def safe_insert(db, model, data):
    """安全插入，如果已存在则跳过"""
    try:
        existing = db.query(model).filter_by(**{k: v for k, v in data.items() if hasattr(model, k)}).first()
        if not existing:
            instance = model(**data)
            db.add(instance)
            db.commit()
        return True
    except Exception as e:
        db.rollback()
        return False


def init_test_data():
    """初始化测试数据"""
    print("=" * 60)
    print("开始初始化测试数据...")
    print("=" * 60)

    db = SessionLocal()

    try:
        # ==================== 项目组数据 ====================
        print("\n--- 初始化项目组 ---")

        # 获取项目经理用户
        pm_user = db.query(User).filter(User.username == "zhang_pm").first()
        engineer_user = db.query(User).filter(User.username == "lisi_eng").first()
        designer_user = db.query(User).filter(User.username == "zhangsan").first()

        project_groups = [
            {
                "id": "pg_001",
                "name": "智能控制器项目组",
                "code": "PG-CTRL-001",
                "leader_id": pm_user.id,
                "department_id": "dept_rd1",
                "status": "active"
            },
            {
                "id": "pg_002",
                "name": "电机驱动项目组",
                "code": "PG-MOTOR-001",
                "leader_id": pm_user.id,
                "department_id": "dept_rd1",
                "status": "active"
            },
            {
                "id": "pg_003",
                "name": "传感系统项目组",
                "code": "PG-SENSOR-001",
                "leader_id": pm_user.id,
                "department_id": "dept_rd1",
                "status": "active"
            },
        ]

        for pg_data in project_groups:
            existing = db.query(ProjectGroup).filter(ProjectGroup.code == pg_data["code"]).first()
            if existing:
                print(f"  项目组已存在: {pg_data['name']}")
            else:
                pg = ProjectGroup(**pg_data)
                db.add(pg)
                db.commit()
                print(f"✓ 项目组: {pg_data['name']} ({pg_data['code']})")

        # 添加项目组成员
        from app.models.project_group import project_group_members
        from sqlalchemy import insert, text

        def add_member(group_id, user_id, role_type):
            """添加成员，如果已存在则跳过"""
            try:
                existing = db.execute(
                    text("SELECT 1 FROM project_group_members WHERE group_id = :gid AND user_id = :uid"),
                    {"gid": group_id, "uid": user_id}
                ).fetchone()
                if existing:
                    return False
                db.execute(insert(project_group_members).values(
                    group_id=group_id,
                    user_id=user_id,
                    role_type=role_type
                ))
                db.commit()
                return True
            except Exception:
                db.rollback()
                return False

        # 智能控制器项目组成员
        if add_member("pg_001", pm_user.id, "manager"):
            print(f"✓ 添加项目经理到智能控制器项目组")
        else:
            print(f"  项目经理已在智能控制器项目组中")
        if add_member("pg_001", engineer_user.id, "engineer"):
            print(f"✓ 添加工程师到智能控制器项目组")
        if add_member("pg_001", designer_user.id, "engineer"):
            print(f"✓ 添加设计师到智能控制器项目组")

        # 电机驱动项目组成员
        if add_member("pg_002", pm_user.id, "manager"):
            print(f"✓ 添加项目经理到电机驱动项目组")
        else:
            print(f"  项目经理已在电机驱动项目组中")
        if add_member("pg_002", engineer_user.id, "engineer"):
            print(f"✓ 添加工程师到电机驱动项目组")

        # 传感系统项目组成员
        if add_member("pg_003", pm_user.id, "manager"):
            print(f"✓ 添加项目经理到传感系统项目组")
        else:
            print(f"  项目经理已在传感系统项目组中")
        if add_member("pg_003", designer_user.id, "engineer"):
            print(f"✓ 添加设计师到传感系统项目组")

        # ==================== 产品数据 ====================
        print("\n--- 初始化产品 ---")

        products = [
            {
                "id": "prod_001",
                "name": "智能控制器 V1.0",
                "code": "CTRL-V100",
                "status": "active",
                "project_group_id": "pg_001",
                "department_id": "dept_rd1",
                "manager": "张项目经理",
                "start_date": date(2026, 1, 1)
            },
            {
                "id": "prod_002",
                "name": "智能控制器 V2.0",
                "code": "CTRL-V200",
                "status": "active",
                "project_group_id": "pg_001",
                "department_id": "dept_rd1",
                "manager": "张项目经理",
                "start_date": date(2026, 3, 1)
            },
            {
                "id": "prod_003",
                "name": "直流无刷电机驱动",
                "code": "MOTOR-BLDC",
                "status": "active",
                "project_group_id": "pg_002",
                "department_id": "dept_rd1",
                "manager": "张项目经理",
                "start_date": date(2026, 2, 1)
            },
            {
                "id": "prod_004",
                "name": "伺服电机驱动器",
                "code": "MOTOR-SERVO",
                "status": "active",
                "project_group_id": "pg_002",
                "department_id": "dept_rd1",
                "manager": "张项目经理",
                "start_date": date(2026, 3, 15)
            },
            {
                "id": "prod_005",
                "name": "温度传感器模块",
                "code": "SENSOR-TEMP",
                "status": "active",
                "project_group_id": "pg_003",
                "department_id": "dept_rd1",
                "manager": "张项目经理",
                "start_date": date(2026, 2, 15)
            },
            {
                "id": "prod_006",
                "name": "压力传感器模块",
                "code": "SENSOR-PRES",
                "status": "archived",
                "project_group_id": "pg_003",
                "department_id": "dept_rd1",
                "manager": "张项目经理",
                "start_date": date(2025, 10, 1)
            },
        ]

        for prod_data in products:
            existing = db.query(Product).filter(Product.code == prod_data["code"]).first()
            if existing:
                print(f"  产品已存在: {prod_data['name']}")
            else:
                prod = Product(**prod_data)
                db.add(prod)
                db.commit()
                print(f"✓ 产品: {prod_data['name']} ({prod_data['code']})")

        # ==================== 图纸数据 ====================
        print("\n--- 初始化图纸 ---")

        drawings = [
            {
                "id": "draw_001",
                "drawing_no": "CTRL-V100-0001",
                "name": "控制器主板原理图",
                "product_id": "prod_001",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "creator_id": designer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "智能控制器V1.0主板电路设计，用于产品主控",
                "material": "FR-4 PCB, 4层板",
                "dimensions": "100mm x 80mm",
                "secret_points": "核心控制算法硬件实现，芯片选型方案"
            },
            {
                "id": "draw_002",
                "drawing_no": "CTRL-V100-0002",
                "name": "控制器外壳设计图",
                "product_id": "prod_001",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.C,
                "is_core_part": False,
                "creator_id": designer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "产品外壳结构设计",
                "material": "ABS塑料",
                "dimensions": "120mm x 100mm x 50mm"
            },
            {
                "id": "draw_003",
                "drawing_no": "CTRL-V100-0003",
                "name": "电源模块电路图",
                "product_id": "prod_001",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.A,
                "is_core_part": True,
                "creator_id": engineer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "核心电源管理方案",
                "material": "PCB板",
                "dimensions": "60mm x 40mm",
                "secret_points": "专利电源转换技术，效率优化方案"
            },
            {
                "id": "draw_004",
                "drawing_no": "CTRL-V200-0001",
                "name": "V2.0控制器主板原理图",
                "product_id": "prod_002",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.A,
                "is_core_part": True,
                "creator_id": designer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "V2.0版本核心控制板设计",
                "material": "高频PCB板",
                "dimensions": "110mm x 90mm",
                "secret_points": "新一代控制算法硬件实现，性能优化"
            },
            {
                "id": "draw_005",
                "drawing_no": "CTRL-V200-0002",
                "name": "V2.0通信接口设计",
                "product_id": "prod_002",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "creator_id": engineer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "新增CAN和Ethernet接口设计",
                "material": "PCB板",
                "dimensions": "50mm x 30mm",
                "secret_points": "通信协议栈硬件实现"
            },
            {
                "id": "draw_006",
                "drawing_no": "MOTOR-BLDC-0001",
                "name": "BLDC驱动器原理图",
                "product_id": "prod_003",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.A,
                "is_core_part": True,
                "creator_id": engineer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "直流无刷电机驱动控制方案",
                "material": "铝基板PCB",
                "dimensions": "80mm x 60mm",
                "secret_points": "FOC控制算法硬件实现"
            },
            {
                "id": "draw_007",
                "drawing_no": "MOTOR-BLDC-0002",
                "name": "功率模块设计图",
                "product_id": "prod_003",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "creator_id": designer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.REJECTED,
                "purpose": "电机功率驱动部分设计",
                "material": "IGBT模块",
                "dimensions": "100mm x 70mm",
                "secret_points": "功率器件散热设计"
            },
            {
                "id": "draw_008",
                "drawing_no": "SENSOR-TEMP-0001",
                "name": "温度传感器封装图",
                "product_id": "prod_005",
                "department_id": "dept_rd1",
                "confidentiality_level": ConfidentialityLevel.C,
                "is_core_part": False,
                "creator_id": designer_user.id,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "温度传感器结构设计",
                "material": "不锈钢外壳",
                "dimensions": "φ10mm x 30mm"
            },
        ]

        for draw_data in drawings:
            existing = db.query(Drawing).filter(Drawing.drawing_no == draw_data["drawing_no"]).first()
            if existing:
                print(f"  图纸已存在: {draw_data['drawing_no']}")
            else:
                drawing = Drawing(**draw_data)
                db.add(drawing)
                db.commit()
                print(f"✓ 图纸: {draw_data['drawing_no']} - {draw_data['name']}")

        # ==================== 图纸版本数据 ====================
        print("\n--- 初始化图纸版本 ---")

        versions = [
            {"id": "ver_001", "drawing_id": "draw_001", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_001/V1.0/drawing.dwg",
             "file_name": "控制器主板原理图_V1.0.dwg", "file_size": 2048000,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": designer_user.id, "uploaded_at": datetime.now() - timedelta(days=30), "is_latest": True},
            {"id": "ver_002", "drawing_id": "draw_002", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_002/V1.0/drawing.dwg",
             "file_name": "控制器外壳设计图_V1.0.dwg", "file_size": 1536000,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": designer_user.id, "uploaded_at": datetime.now() - timedelta(days=25), "is_latest": True},
            {"id": "ver_003", "drawing_id": "draw_003", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_003/V1.0/drawing.dwg",
             "file_name": "电源模块电路图_V1.0.dwg", "file_size": 1024000,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": engineer_user.id, "uploaded_at": datetime.now() - timedelta(days=2), "is_latest": True},
            {"id": "ver_004", "drawing_id": "draw_004", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_004/V1.0/drawing.dwg",
             "file_name": "V2.0控制器主板原理图_V1.0.dwg", "file_size": 2560000,
             "file_format": "DWG", "change_types": "initial", "change_reason": "V2.0初始版本",
             "uploader_id": designer_user.id, "uploaded_at": datetime.now() - timedelta(days=1), "is_latest": True},
            {"id": "ver_005", "drawing_id": "draw_005", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_005/V1.0/drawing.dwg",
             "file_name": "V2.0通信接口设计_V1.0.dwg", "file_size": 512000,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": engineer_user.id, "uploaded_at": datetime.now() - timedelta(days=3), "is_latest": True},
            {"id": "ver_006", "drawing_id": "draw_006", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_006/V1.0/drawing.dwg",
             "file_name": "BLDC驱动器原理图_V1.0.dwg", "file_size": 1843200,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": engineer_user.id, "uploaded_at": datetime.now() - timedelta(days=15), "is_latest": True},
            {"id": "ver_007", "drawing_id": "draw_007", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_007/V1.0/drawing.dwg",
             "file_name": "功率模块设计图_V1.0.dwg", "file_size": 819200,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": designer_user.id, "uploaded_at": datetime.now() - timedelta(days=5), "is_latest": True},
            {"id": "ver_008", "drawing_id": "draw_008", "version_no": "V1.0",
             "file_path": "/data/drawings/draw_008/V1.0/drawing.dwg",
             "file_name": "温度传感器封装图_V1.0.dwg", "file_size": 409600,
             "file_format": "DWG", "change_types": "initial", "change_reason": "初始版本",
             "uploader_id": designer_user.id, "uploaded_at": datetime.now() - timedelta(days=1), "is_latest": True},
        ]

        for ver_data in versions:
            existing = db.query(DrawingVersion).filter(
                DrawingVersion.drawing_id == ver_data["drawing_id"],
                DrawingVersion.version_no == ver_data["version_no"]
            ).first()
            if existing:
                print(f"  版本已存在: {ver_data['drawing_id']} {ver_data['version_no']}")
            else:
                version = DrawingVersion(**ver_data)
                db.add(version)
                db.commit()
                print(f"✓ 版本: {ver_data['drawing_id']} - {ver_data['version_no']}")

        # ==================== 审核历史数据 ====================
        print("\n--- 初始化审核历史 ---")

        review_histories = [
            {"id": "rh_001", "drawing_id": "draw_001", "old_level": "C", "new_level": "B",
             "reason": "经审核，该图纸涉及核心控制算法，调整为B类保密",
             "reviewer_id": pm_user.id, "reviewer_name": "张项目经理",
             "created_at": datetime.now() - timedelta(days=28)},
            {"id": "rh_002", "drawing_id": "draw_002", "old_level": "B", "new_level": "C",
             "reason": "外壳设计不属于核心技术，调整为C类",
             "reviewer_id": pm_user.id, "reviewer_name": "张项目经理",
             "created_at": datetime.now() - timedelta(days=24)},
            {"id": "rh_003", "drawing_id": "draw_006", "old_level": "C", "new_level": "A",
             "reason": "FOC控制算法为本公司核心技术，升级为A类保密",
             "reviewer_id": pm_user.id, "reviewer_name": "张项目经理",
             "created_at": datetime.now() - timedelta(days=14)},
            {"id": "rh_004", "drawing_id": "draw_007", "old_level": "C", "new_level": "B",
             "reason": "初始审核",
             "reviewer_id": pm_user.id, "reviewer_name": "张项目经理",
             "created_at": datetime.now() - timedelta(days=4)},
            {"id": "rh_005", "drawing_id": "draw_007", "old_level": "B", "new_level": "B",
             "reason": "功率模块散热设计需要优化，请重新提交",
             "reviewer_id": pm_user.id, "reviewer_name": "张项目经理",
             "created_at": datetime.now() - timedelta(days=4, hours=2)},
        ]

        for rh_data in review_histories:
            try:
                db.execute(
                    text("""
                        INSERT INTO review_history (id, drawing_id, old_level, new_level, reason, reviewer_id, reviewer_name, created_at)
                        VALUES (:id, :drawing_id, :old_level, :new_level, :reason, :reviewer_id, :reviewer_name, :created_at)
                    """),
                    rh_data
                )
                db.commit()
                print(f"✓ 审核历史: {rh_data['drawing_id']} - {rh_data['old_level']} -> {rh_data['new_level']}")
            except Exception as e:
                db.rollback()
                print(f"  审核历史已存在: {rh_data['drawing_id']}")

        print("\n" + "=" * 60)
        print("✓ 测试数据初始化完成!")
        print("=" * 60)

        print("\n测试数据摘要:")
        print(f"  - 项目组: 3 个")
        print(f"    * 智能控制器项目组 (PG-CTRL-001)")
        print(f"    * 电机驱动项目组 (PG-MOTOR-001)")
        print(f"    * 传感系统项目组 (PG-SENSOR-001)")
        print(f"\n  - 产品: 6 个")
        print(f"    * CTRL-V100 (智能控制器 V1.0) - 进行中")
        print(f"    * CTRL-V200 (智能控制器 V2.0) - 进行中")
        print(f"    * MOTOR-BLDC (直流无刷电机驱动) - 进行中")
        print(f"    * MOTOR-SERVO (伺服电机驱动器) - 进行中")
        print(f"    * SENSOR-TEMP (温度传感器模块) - 进行中")
        print(f"    * SENSOR-PRES (压力传感器模块) - 已归档")
        print(f"\n  - 图纸: 8 张")
        print(f"    * 已通过审核: 2 张")
        print(f"    * 待审核: 5 张")
        print(f"    * 已驳回: 1 张")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_test_data()
