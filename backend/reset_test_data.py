#!/usr/bin/env python
"""
重置测试数据脚本
生成高质量的测试数据，包括：
- 项目组、产品
- 图纸及其多个历史版本（每个版本有真实差异内容）
- 审核历史
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from sqlalchemy import insert, text
from datetime import datetime, timedelta, date
from app.core.database import SessionLocal
from app.models import User, Role, Department, Product, ProjectGroup
from app.models.project_group import project_group_members
from app.models.drawing import Drawing, DrawingVersion, DrawingStatus, ReviewStatus, ConfidentialityLevel


def safe_delete(db, model):
    """清空表数据"""
    try:
        db.query(model).delete()
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"  清空 {model.__name__} 失败: {e}")


def add_member(db, group_id, user_id, role_type):
    """添加项目组成员"""
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


def generate_version_file(storage_path, drawing_no, version_no, version_info):
    """
    生成版本文件，每个版本有唯一内容便于区分
    文件格式：JSON 描述图纸版本差异
    """
    os.makedirs(storage_path, exist_ok=True)

    file_data = {
        "drawing_no": drawing_no,
        "version": version_no,
        "generated_at": datetime.now().isoformat(),
        "description": version_info.get("description") or version_info.get("change_reason", ""),
        "change_details": version_info.get("change_details", []),
        "specifications": version_info.get("specifications", {}),
        "remarks": version_info.get("remarks", "")
    }

    file_path = os.path.join(storage_path, "drawing.json")
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(file_data, f, ensure_ascii=False, indent=2)

    # 同时创建一个文本文件说明版本差异
    txt_path = os.path.join(storage_path, "version_info.txt")
    version_desc = version_info.get("description") or version_info.get("change_reason", "")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(f"图纸编号: {drawing_no}\n")
        f.write(f"版本号: {version_no}\n")
        f.write(f"生成时间: {datetime.now().isoformat()}\n")
        f.write(f"\n版本说明: {version_desc}\n")
        if version_info.get("change_details"):
            f.write("\n变更详情:\n")
            for detail in version_info["change_details"]:
                f.write(f"  - {detail}\n")
        if version_info.get("remarks"):
            f.write(f"\n备注: {version_info['remarks']}\n")

    # 计算文件大小
    file_size = os.path.getsize(file_path) + os.path.getsize(txt_path)
    return file_path, file_size


def reset_test_data():
    """重置测试数据"""
    print("=" * 60)
    print("开始重置测试数据...")
    print("=" * 60)

    db = SessionLocal()

    try:
        # ==================== 清空现有业务数据 ====================
        print("\n--- 清空现有数据 ---")

        # 清空顺序很重要（外键关联）
        safe_delete(db, DrawingVersion)
        print("  ✓ 清空图纸版本")
        safe_delete(db, Drawing)
        print("  ✓ 清空图纸")
        safe_delete(db, Product)
        print("  ✓ 清空产品")
        safe_delete(db, ProjectGroup)
        print("  ✓ 清空项目组")

        # 清空项目组成员的关联表
        try:
            db.execute(text("DELETE FROM project_group_members"))
            db.commit()
            print("  ✓ 清空项目组成员")
        except Exception:
            db.rollback()

        # 清空审核历史表
        try:
            db.execute(text("DELETE FROM review_history"))
            db.commit()
            print("  ✓ 清空审核历史")
        except Exception:
            db.rollback()

        # ==================== 获取用户 ====================
        print("\n--- 获取用户账户 ---")

        # 使用 init_db.py 创建的标准用户
        users = {
            "admin": db.query(User).filter(User.username == "admin").first(),
            "cto": db.query(User).filter(User.username == "cto").first(),
            "zhang": db.query(User).filter(User.username == "zhang").first(),  # 项目经理
            "lisi": db.query(User).filter(User.username == "lisi").first(),    # 工程师
            "zhangsan": db.query(User).filter(User.username == "zhangsan").first(),  # 设计师
            "lishen": db.query(User).filter(User.username == "lishen").first(),  # 审定人
            "archivemgr": db.query(User).filter(User.username == "archivemgr").first(),  # 档案管理员
        }

        for username, user in users.items():
            if user:
                print(f"  ✓ 用户 {username}: {user.name}")
            else:
                print(f"  ✗ 用户 {username} 不存在，跳过")

        # ==================== 创建项目组 ====================
        print("\n--- 创建项目组 ---")

        project_groups = [
            {
                "id": "pg_001",
                "name": "智能控制器项目组",
                "code": "PG-CTRL-001",
                "leader_id": users["zhang"].id if users["zhang"] else None,
                "department_id": "dept_rd1",
                "status": "active"
            },
            {
                "id": "pg_002",
                "name": "电机驱动项目组",
                "code": "PG-MOTOR-001",
                "leader_id": users["zhang"].id if users["zhang"] else None,
                "department_id": "dept_rd1",
                "status": "active"
            },
            {
                "id": "pg_003",
                "name": "传感系统项目组",
                "code": "PG-SENSOR-001",
                "leader_id": users["zhang"].id if users["zhang"] else None,
                "department_id": "dept_rd1",
                "status": "active"
            },
        ]

        for pg_data in project_groups:
            pg = ProjectGroup(**pg_data)
            db.add(pg)
            db.commit()
            print(f"  ✓ 项目组: {pg_data['name']} ({pg_data['code']})")

            # 添加项目经理到所有项目组
            if users["zhang"]:
                add_member(db, pg_data["id"], users["zhang"].id, "manager")

        # 添加工程师和设计师到项目组
        if users["lisi"]:
            add_member(db, "pg_001", users["lisi"].id, "engineer")
            add_member(db, "pg_002", users["lisi"].id, "engineer")
            print("  ✓ 添加李工程师到控制器和电机项目组")

        if users["zhangsan"]:
            add_member(db, "pg_001", users["zhangsan"].id, "engineer")
            add_member(db, "pg_003", users["zhangsan"].id, "engineer")
            print("  ✓ 添加张设计师到控制器和传感器项目组")

        # ==================== 创建产品 ====================
        print("\n--- 创建产品 ---")

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
            prod = Product(**prod_data)
            db.add(prod)
            db.commit()
            status_tag = "[进行中]" if prod_data["status"] == "active" else "[已归档]"
            print(f"  ✓ 产品: {prod_data['name']} ({prod_data['code']}) {status_tag}")

        # ==================== 图纸及版本数据 ====================
        print("\n--- 创建图纸及版本 ---")

        # 图纸版本设计 - 每个图纸有多个版本，版本之间有真实差异
        drawings_config = [
            {
                "drawing_no": "CTRL-V100-0001",
                "name": "控制器主板原理图",
                "product_id": "prod_001",
                "creator": "zhangsan",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "智能控制器V1.0主板电路设计，用于产品主控",
                "material": "FR-4 PCB, 4层板",
                "dimensions": "100mm x 80mm",
                "secret_points": "核心控制算法硬件实现，芯片选型方案",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始版本，基础原理图设计完成",
                        "change_details": [
                            "主控芯片STM32F407选型",
                            "最小系统电路设计",
                            "电源电路基础设计"
                        ],
                        "specifications": {"chip": "STM32F407", "layers": 4, "size": "100x80mm"},
                        "remarks": "第一版原理图，验证基本架构"
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "修正电源滤波电路参数，优化EMC性能",
                        "change_details": [
                            "电源输入端增加共模滤波器",
                            "晶振电路周围增加接地铺铜",
                            "调整去耦电容位置"
                        ],
                        "specifications": {"chip": "STM32F407", "emc": "enhanced", "layers": 4},
                        "remarks": "EMC优化第一版"
                    },
                    {
                        "version_no": "V1.2",
                        "change_types": "major_change",
                        "change_reason": "主控芯片升级为STM32H7，增加外设接口",
                        "change_details": [
                            "芯片升级：STM32F407 → STM32H743",
                            "新增CAN接口电路",
                            "新增Ethernet接口电路",
                            "USB OTG接口重新设计"
                        ],
                        "specifications": {"chip": "STM32H743", "can": 2, "ethernet": 1, "usb": "OTG"},
                        "remarks": "重大升级，性能大幅提升"
                    },
                    {
                        "version_no": "V1.3",
                        "change_types": "minor_revision",
                        "change_reason": "调整晶振电路布局，降低干扰",
                        "change_details": [
                            "晶振远离电源输入端",
                            "时钟线增加保护环",
                            "备份电源电路优化"
                        ],
                        "specifications": {"chip": "STM32H743", "clock": "optimized"},
                        "remarks": "针对V1.2布局优化"
                    },
                    {
                        "version_no": "V2.0",
                        "change_types": "function_addition",
                        "change_reason": "新增CAN通信接口，重新布局，支持更多工业协议",
                        "change_details": [
                            "新增第2路CAN接口",
                            "RS485接口升级为隔离型",
                            "新增SWD调试接口",
                            "整版重新布局布线"
                        ],
                        "specifications": {"chip": "STM32H743", "can": 2, "rs485": "isolated", "protocols": "Modbus/CANopen"},
                        "remarks": "正式发布版本"
                    }
                ]
            },
            {
                "drawing_no": "CTRL-V100-0002",
                "name": "控制器外壳设计图",
                "product_id": "prod_001",
                "creator": "zhangsan",
                "confidentiality_level": ConfidentialityLevel.C,
                "is_core_part": False,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "产品外壳结构设计",
                "material": "ABS塑料",
                "dimensions": "120mm x 100mm x 50mm",
                "secret_points": "外观专利",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始版本外壳设计",
                        "change_details": ["基础外壳模型", "安装孔位设计"],
                        "specifications": {"material": "ABS", "size": "120x100x50mm"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "优化散热孔布局，增加强度",
                        "change_details": ["侧面散热孔直径调整", "加强筋结构优化"],
                        "specifications": {"material": "ABS", "size": "120x100x50mm", "cooling": "improved"}
                    },
                    {
                        "version_no": "V2.0",
                        "change_types": "major_change",
                        "change_reason": "重新开模，尺寸调整以适配V2.0主板",
                        "change_details": ["高度增加5mm", "内部结构重新设计", "防水密封圈槽"],
                        "specifications": {"material": "ABS", "size": "120x100x55mm", "waterproof": True}
                    }
                ]
            },
            {
                "drawing_no": "CTRL-V100-0003",
                "name": "电源模块电路图",
                "product_id": "prod_001",
                "creator": "lisi",
                "confidentiality_level": ConfidentialityLevel.A,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "核心电源管理方案",
                "material": "PCB板",
                "dimensions": "60mm x 40mm",
                "secret_points": "专利电源转换技术，效率优化方案",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始版本电源模块设计",
                        "change_details": ["12V转5V设计", "5V转3.3V设计", "基础保护电路"],
                        "specifications": {"input": "12V", "outputs": ["5V/2A", "3.3V/1A"], "efficiency": ">85%"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "优化转换效率，增加软启动电路",
                        "change_details": ["效率优化到92%", "增加软启动电路", "瞬态响应改善"],
                        "specifications": {"input": "12V", "outputs": ["5V/2A", "3.3V/1A"], "efficiency": ">92%"}
                    },
                    {
                        "version_no": "V2.0",
                        "change_types": "major_change",
                        "change_reason": "新增24V输入支持，宽电压输入范围",
                        "change_details": ["支持12V-24V输入", "效率优化到95%", "过热保护阈值调整"],
                        "specifications": {"input": "12V-24V", "outputs": ["5V/3A", "3.3V/1.5A"], "efficiency": ">95%"}
                    }
                ]
            },
            {
                "drawing_no": "CTRL-V200-0001",
                "name": "V2.0控制器主板原理图",
                "product_id": "prod_002",
                "creator": "zhangsan",
                "confidentiality_level": ConfidentialityLevel.A,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "V2.0版本核心控制板设计",
                "material": "高频PCB板",
                "dimensions": "110mm x 90mm",
                "secret_points": "新一代控制算法硬件实现，性能优化",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "V2.0初始设计，基于V1.0优化",
                        "change_details": ["全新主芯片STM32H743", "双CAN接口", "千兆以太网"],
                        "specifications": {"chip": "STM32H743", "can": 2, "ethernet": "Gigabit"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "修正USB接口电路问题",
                        "change_details": ["USB差分线重新走线", "ESD保护增强"],
                        "specifications": {"chip": "STM32H743", "usb": "corrected"}
                    },
                    {
                        "version_no": "V2.0",
                        "change_types": "function_addition",
                        "change_reason": "新增TSN时间同步接口，完整V2.0设计定稿",
                        "change_details": ["TSN接口设计", "双Flash冗余存储", "看门狗增强"],
                        "specifications": {"chip": "STM32H743", "tsn": True, "flash": "dual"}
                    }
                ]
            },
            {
                "drawing_no": "CTRL-V200-0002",
                "name": "V2.0通信接口设计",
                "product_id": "prod_002",
                "creator": "lisi",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "新增CAN和Ethernet接口设计",
                "material": "PCB板",
                "dimensions": "50mm x 30mm",
                "secret_points": "通信协议栈硬件实现",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始通信接口设计",
                        "change_details": ["CAN接口电路", "Ethernet PHY电路"],
                        "specifications": {"can": 1, "ethernet": "100M"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "major_change",
                        "change_reason": "升级为双路CAN，新增CANopen协议支持",
                        "change_details": ["第2路CAN接口", "CANopen协议芯片", "隔离变压器"],
                        "specifications": {"can": 2, "ethernet": "100M", "protocol": "CANopen"}
                    }
                ]
            },
            {
                "drawing_no": "MOTOR-BLDC-0001",
                "name": "BLDC驱动器原理图",
                "product_id": "prod_003",
                "creator": "lisi",
                "confidentiality_level": ConfidentialityLevel.A,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "直流无刷电机驱动控制方案",
                "material": "铝基板PCB",
                "dimensions": "80mm x 60mm",
                "secret_points": "FOC控制算法硬件实现",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始版本BLDC驱动设计",
                        "change_details": ["三相H桥设计", "电流采样电路", "基础保护"],
                        "specifications": {"phases": 3, "current": "10A", "control": "6-step"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "增加过流保护阈值，调整栅极驱动",
                        "change_details": ["过流保护点调整", "栅极电阻优化", "死区时间调整"],
                        "specifications": {"phases": 3, "current": "10A", "protection": "enhanced"}
                    },
                    {
                        "version_no": "V2.0",
                        "change_types": "major_change",
                        "change_reason": "升级为FOC控制算法，完整硬件支持",
                        "change_details": ["FOC算法硬件实现", "编码器接口", "速度反馈"],
                        "specifications": {"phases": 3, "current": "15A", "control": "FOC", "encoder": True}
                    }
                ]
            },
            {
                "drawing_no": "MOTOR-BLDC-0002",
                "name": "功率模块设计图",
                "product_id": "prod_003",
                "creator": "zhangsan",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.REJECTED,
                "purpose": "电机功率驱动部分设计",
                "material": "IGBT模块",
                "dimensions": "100mm x 70mm",
                "secret_points": "功率器件散热设计",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始功率模块设计",
                        "change_details": ["IGBT驱动电路", "散热片安装设计"],
                        "specifications": {"power": "1kW", "igbt": 6, "cooling": "passive"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "优化散热设计，增加温度检测",
                        "change_details": ["散热片尺寸调整", "新增温度传感器", "热仿真验证"],
                        "specifications": {"power": "1kW", "igbt": 6, "cooling": "active", "temp_sensor": True}
                    }
                ]
            },
            {
                "drawing_no": "SENSOR-TEMP-0001",
                "name": "温度传感器封装图",
                "product_id": "prod_005",
                "creator": "zhangsan",
                "confidentiality_level": ConfidentialityLevel.C,
                "is_core_part": False,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.PENDING,
                "purpose": "温度传感器结构设计",
                "material": "不锈钢外壳",
                "dimensions": "φ10mm x 30mm",
                "secret_points": "无",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始封装设计",
                        "change_details": ["探头设计", "密封结构", "安装螺纹"],
                        "specifications": {"material": "SS304", "size": "10x30mm", "temp_range": "-40~150C"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "优化密封结构，提高防水等级",
                        "change_details": ["IP68防水设计", "出线口密封", "耐压测试验证"],
                        "specifications": {"material": "SS304", "size": "10x30mm", "ip_rating": "IP68"}
                    }
                ]
            },
            {
                "drawing_no": "SENSOR-PRES-0001",
                "name": "压力传感器模块电路",
                "product_id": "prod_006",
                "creator": "lisi",
                "confidentiality_level": ConfidentialityLevel.B,
                "is_core_part": True,
                "status": DrawingStatus.ACTIVE,
                "review_status": ReviewStatus.APPROVED,
                "purpose": "压力传感器信号处理电路",
                "material": "PCB板",
                "dimensions": "25mm x 15mm",
                "secret_points": "信号放大电路设计",
                "versions": [
                    {
                        "version_no": "V1.0",
                        "change_types": "initial",
                        "change_reason": "初始版本设计",
                        "change_details": ["压力传感器接口", "信号放大电路", "温度补偿"],
                        "specifications": {"pressure_range": "0-10MPa", "output": "4-20mA"}
                    },
                    {
                        "version_no": "V1.1",
                        "change_types": "minor_revision",
                        "change_reason": "优化温漂性能",
                        "change_details": ["温度补偿算法优化", "零点漂移调整", "精度提升"],
                        "specifications": {"pressure_range": "0-10MPa", "output": "4-20mA", "accuracy": "0.5%"}
                    }
                ]
            },
        ]

        # 存储根路径
        base_storage_path = "./data/drawings"

        for draw_cfg in drawings_config:
            creator = users.get(draw_cfg["creator"])
            if not creator:
                print(f"  ✗ 图纸 {draw_cfg['drawing_no']} 创建者不存在，跳过")
                continue

            # 创建图纸
            drawing = Drawing(
                drawing_no=draw_cfg["drawing_no"],
                name=draw_cfg["name"],
                product_id=draw_cfg["product_id"],
                department_id="dept_rd1",
                confidentiality_level=draw_cfg["confidentiality_level"],
                is_core_part=draw_cfg["is_core_part"],
                creator_id=creator.id,
                status=draw_cfg["status"],
                review_status=draw_cfg["review_status"],
                purpose=draw_cfg.get("purpose"),
                material=draw_cfg.get("material"),
                dimensions=draw_cfg.get("dimensions"),
                secret_points=draw_cfg.get("secret_points")
            )
            db.add(drawing)
            db.commit()

            # 创建版本
            for i, ver_cfg in enumerate(draw_cfg["versions"]):
                version_no = ver_cfg["version_no"]
                is_latest = (i == len(draw_cfg["versions"]) - 1)  # 最后一个版本是最新

                # 生成版本文件
                version_path = os.path.join(base_storage_path, drawing.id, version_no)
                file_path, file_size = generate_version_file(
                    version_path,
                    draw_cfg["drawing_no"],
                    version_no,
                    ver_cfg
                )

                # 计算版本上传时间（从现在往回推，越新的版本时间越近）
                days_ago = 30 - (i * 7)  # 每7天一个版本
                uploaded_at = datetime.now() - timedelta(days=days_ago)

                version = DrawingVersion(
                    drawing_id=drawing.id,
                    version_no=version_no,
                    file_path=file_path,
                    file_name=f"{draw_cfg['drawing_no']}_{version_no}.json",
                    file_size=file_size,
                    file_format="JSON",
                    change_types=ver_cfg["change_types"],
                    change_reason=ver_cfg["change_reason"],
                    uploader_id=creator.id,
                    uploaded_at=uploaded_at,
                    is_latest=is_latest
                )
                db.add(version)
                db.commit()

                latest_tag = " [最新版本]" if is_latest else ""
                print(f"    ✓ {draw_cfg['drawing_no']} {version_no}: {ver_cfg['change_reason'][:30]}...{latest_tag}")

            print(f"  ✓ 图纸: {draw_cfg['drawing_no']} - {draw_cfg['name']} ({len(draw_cfg['versions'])}个版本)")

        # ==================== 审核历史 ====================
        print("\n--- 创建审核历史 ---")

        review_histories = [
            {
                "id": "rh_001",
                "drawing_no": "CTRL-V100-0001",
                "old_level": "C",
                "new_level": "B",
                "reason": "经审核，该图纸涉及核心控制算法，调整为B类保密",
                "reviewer_name": "张项目经理",
                "created_at": datetime.now() - timedelta(days=28)
            },
            {
                "id": "rh_002",
                "drawing_no": "CTRL-V100-0002",
                "old_level": "B",
                "new_level": "C",
                "reason": "外壳设计不属于核心技术，调整为C类",
                "reviewer_name": "张项目经理",
                "created_at": datetime.now() - timedelta(days=24)
            },
            {
                "id": "rh_003",
                "drawing_no": "MOTOR-BLDC-0001",
                "old_level": "C",
                "new_level": "A",
                "reason": "FOC控制算法为本公司核心技术，升级为A类保密",
                "reviewer_name": "张项目经理",
                "created_at": datetime.now() - timedelta(days=14)
            },
            {
                "id": "rh_004",
                "drawing_no": "MOTOR-BLDC-0002",
                "old_level": "C",
                "new_level": "B",
                "reason": "初始审核",
                "reviewer_name": "张项目经理",
                "created_at": datetime.now() - timedelta(days=4)
            },
            {
                "id": "rh_005",
                "drawing_no": "MOTOR-BLDC-0002",
                "old_level": "B",
                "new_level": "B",
                "reason": "功率模块散热设计需要优化，请重新提交",
                "reviewer_name": "张项目经理",
                "created_at": datetime.now() - timedelta(days=4, hours=2)
            },
        ]

        for rh in review_histories:
            # 获取图纸ID
            drawing = db.query(Drawing).filter(Drawing.drawing_no == rh["drawing_no"]).first()
            if not drawing:
                continue

            # 获取审核人ID
            reviewer = db.query(User).filter(User.name.like(f"%{rh['reviewer_name'].replace('张项目经理', '张经理')}%")).first()
            if not reviewer:
                reviewer = users["zhang"]

            try:
                db.execute(
                    text("""
                        INSERT INTO review_history (id, drawing_id, old_level, new_level, reason, reviewer_id, reviewer_name, created_at)
                        VALUES (:id, :drawing_id, :old_level, :new_level, :reason, :reviewer_id, :reviewer_name, :created_at)
                    """),
                    {
                        "id": rh["id"],
                        "drawing_id": drawing.id,
                        "old_level": rh["old_level"],
                        "new_level": rh["new_level"],
                        "reason": rh["reason"],
                        "reviewer_id": reviewer.id if reviewer else None,
                        "reviewer_name": rh["reviewer_name"],
                        "created_at": rh["created_at"]
                    }
                )
                db.commit()
                print(f"  ✓ 审核历史: {rh['drawing_no']} {rh['old_level']} → {rh['new_level']}")
            except Exception as e:
                db.rollback()
                print(f"  - 审核历史已存在或跳过: {rh['drawing_no']}")

        # ==================== 统计信息 ====================
        print("\n" + "=" * 60)
        print("✓ 测试数据重置完成!")
        print("=" * 60)

        print("\n数据统计:")
        print(f"  - 项目组: 3 个")
        print(f"  - 产品: 6 个 (5 进行中, 1 已归档)")
        print(f"  - 图纸: {len(drawings_config)} 张")
        print(f"  - 图纸版本: 多个，每张图纸 2-5 个版本")
        print(f"  - 审核历史: {len(review_histories)} 条")

        print("\n测试账号:")
        print("  admin / admin123      (管理员)")
        print("  cto / 123456          (CTO)")
        print("  zhang / 123456       (项目经理)")
        print("  lisi / 123456        (工程师)")
        print("  zhangsan / 123456    (设计师)")
        print("  lishen / 123456      (审定人)")
        print("  archivemgr / 123456  (档案管理员)")

        print("\n图纸版本示例 (CTRL-V100-0001):")
        print("  V1.0 - 初始版本，基础原理图设计完成")
        print("  V1.1 - 修正电源滤波电路参数，优化EMC性能")
        print("  V1.2 - 主控芯片升级为STM32H7，增加外设接口")
        print("  V1.3 - 调整晶振电路布局，降低干扰")
        print("  V2.0 - 新增CAN通信接口，重新布局 [最新版本]")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 重置失败: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    reset_test_data()
