#!/usr/bin/env python
"""
多版本图纸测试数据生成脚本
生成包含多个版本、不同文件格式的测试数据
"""

import sys
import os
import uuid
import random
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models import User
from app.models.drawing import Drawing, DrawingVersion, ReviewStatus, ConfidentialityLevel, DrawingStatus


# 测试文件存储基础目录
DATA_DIR = "/Volumes/256G/mywork/Blueprint Management System Project/data/drawings"


def create_text_file(filepath, content, size=None):
    """创建文本文件"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return filepath


def create_pdf_mock_file(filepath, title, content_lines):
    """创建模拟PDF文件（实际上是文本文件，但内容像PDF）"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"%PDF-1.4\n")
        f.write(f"% Test PDF File: {title}\n")
        f.write("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        f.write("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
        f.write("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n")
        f.write(f"\n%% Title: {title}\n")
        f.write(f"%% Created: {datetime.now().isoformat()}\n")
        for line in content_lines:
            f.write(f"% {line}\n")
        f.write("\n%%EOF\n")
    return filepath


def create_dwg_mock_file(filepath, drawing_no, version_no, content_desc):
    """创建模拟DWG文件（实际上是文本文件）"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"AC1027\n")  # AutoCAD 2007 format marker
        f.write(f"% DWG Test File\n")
        f.write(f"% Drawing No: {drawing_no}\n")
        f.write(f"% Version: {version_no}\n")
        f.write(f"% Description: {content_desc}\n")
        f.write(f"% Created: {datetime.now().isoformat()}\n")
        f.write("\n[HEADER]\n")
        f.write(f"VERSION={version_no}\n")
        f.write(f"DRAWING_NO={drawing_no}\n")
        f.write("\n[ENTITIES]\n")
        f.write("LINE,0,0,100,100\n")
        f.write("CIRCLE,50,50,25\n")
        f.write("\n[END]\n")
    return filepath


def create_multiversion_test_data():
    """创建多版本测试数据"""
    print("=" * 70)
    print("创建多版本图纸测试数据")
    print("=" * 70)

    db = SessionLocal()

    try:
        # 获取用户
        admin_user = db.query(User).filter(User.username == "admin").first()
        engineer_user = db.query(User).filter(User.username == "lisi_eng").first()
        designer_user = db.query(User).filter(User.username == "zhangsan").first()

        if not all([admin_user, engineer_user, designer_user]):
            print("✗ 用户不存在，请先运行 init_db.py")
            return

        # 确保数据目录存在
        os.makedirs(DATA_DIR, exist_ok=True)

        # ========== 图纸1：控制器主板 - 3个版本 (DWG -> PDF -> DWG) ==========
        print("\n--- 创建图纸1：控制器主板原理图 (3个版本) ---")

        drawing1_data = {
            "id": "mv_draw_001",
            "drawing_no": "TEST-CTRL-0001",
            "name": "控制器主板原理图V3",
            "product_id": "prod_001",
            "department_id": "dept_rd1",
            "confidentiality_level": ConfidentialityLevel.B,
            "is_core_part": True,
            "creator_id": designer_user.id,
            "status": DrawingStatus.ACTIVE,
            "review_status": ReviewStatus.APPROVED,
            "purpose": "控制器V3版本主板设计，新增蓝牙模块接口",
            "material": "FR-4 PCB, 6层板",
            "dimensions": "120mm x 100mm",
            "secret_points": "新增蓝牙双模接口，兼容BLE5.0和经典蓝牙"
        }

        # 删除已存在的旧数据
        old_drawing = db.query(Drawing).filter(Drawing.id == "mv_draw_001").first()
        if old_drawing:
            db.query(DrawingVersion).filter(DrawingVersion.drawing_id == "mv_draw_001").delete()
            db.delete(old_drawing)
            db.commit()
            print("  已删除旧数据")

        drawing1 = Drawing(**drawing1_data)
        db.add(drawing1)
        db.commit()
        print(f"✓ 创建图纸: {drawing1_data['drawing_no']} - {drawing1_data['name']}")

        # 版本1 - V1.0 (DWG格式)
        ver1_path = f"{DATA_DIR}/mv_draw_001/V1.0/controller_main_v1.dwg"
        create_dwg_mock_file(ver1_path, drawing1_data['drawing_no'], "V1.0",
                           "Initial design - Basic controller board with USB interface")

        ver1 = DrawingVersion(
            id=str(uuid.uuid4()),
            drawing_id="mv_draw_001",
            version_no="V1.0",
            file_path=ver1_path,
            file_name="控制器主板原理图_V1.0.dwg",
            file_size=os.path.getsize(ver1_path),
            file_format="DWG",
            change_types="initial",
            change_reason="初始版本设计",
            related_issue="",
            uploader_id=designer_user.id,
            uploaded_at=datetime.now() - timedelta(days=60),
            is_latest=False
        )
        db.add(ver1)
        print(f"  ✓ V1.0 - DWG文件 (2.1MB)")

        # 版本2 - V1.1 (PDF格式) - 修复了一些问题
        ver2_path = f"{DATA_DIR}/mv_draw_001/V1.1/controller_main_v1.1.pdf"
        create_pdf_mock_file(ver2_path, "Controller Main Board V1.1",
                           ["Schematic revision 1.1",
                            "Fixed USB power filtering issue",
                            "Added 100uF capacitor on VBUS",
                            "All dimensions verified"])

        ver2 = DrawingVersion(
            id=str(uuid.uuid4()),
            drawing_id="mv_draw_001",
            version_no="V1.1",
            file_path=ver2_path,
            file_name="控制器主板原理图_V1.1.pdf",
            file_size=os.path.getsize(ver2_path),
            file_format="PDF",
            change_types="optimization",
            change_reason="修复USB电源滤波问题，新增滤波电容",
            related_issue="ISSUE-2026-001",
            uploader_id=designer_user.id,
            uploaded_at=datetime.now() - timedelta(days=45),
            is_latest=False
        )
        db.add(ver2)
        print(f"  ✓ V1.1 - PDF文件 (修复版, 1.8MB)")

        # 版本3 - V2.0 (DWG格式) - 重大更新，新增蓝牙
        ver3_path = f"{DATA_DIR}/mv_draw_001/V2.0/controller_main_v2.0.dwg"
        create_dwg_mock_file(ver3_path, drawing1_data['drawing_no'], "V2.0",
                           "Major revision - Added Bluetooth dual-mode interface, "
                           "Upgraded to 6-layer PCB, improved EMC performance")

        ver3 = DrawingVersion(
            id=str(uuid.uuid4()),
            drawing_id="mv_draw_001",
            version_no="V2.0",
            file_path=ver3_path,
            file_name="控制器主板原理图_V2.0.dwg",
            file_size=os.path.getsize(ver3_path),
            file_format="DWG",
            change_types="major_change",
            change_reason="重大更新：新增蓝牙双模接口，升级为6层板，改善EMC性能",
            related_issue="ISSUE-2026-015",
            uploader_id=designer_user.id,
            uploaded_at=datetime.now() - timedelta(days=15),
            is_latest=True
        )
        db.add(ver3)
        print(f"  ✓ V2.0 - DWG文件 (最新版本, 3.2MB)")

        db.commit()

        # ========== 图纸2：电源模块 - 4个版本 (全部PDF) ==========
        print("\n--- 创建图纸2：电源模块设计 (4个版本) ---")

        drawing2_data = {
            "id": "mv_draw_002",
            "drawing_no": "TEST-CTRL-0002",
            "name": "电源模块设计图纸",
            "product_id": "prod_001",
            "department_id": "dept_rd1",
            "confidentiality_level": ConfidentialityLevel.A,
            "is_core_part": True,
            "creator_id": engineer_user.id,
            "status": DrawingStatus.ACTIVE,
            "review_status": ReviewStatus.APPROVED,
            "purpose": "核心电源转换模块，效率优化到95%以上",
            "material": "高频PCB板，带金属基底",
            "dimensions": "80mm x 60mm",
            "secret_points": "专利电源转换技术，效率优化方案，自研PWM控制算法"
        }

        old_drawing = db.query(Drawing).filter(Drawing.id == "mv_draw_002").first()
        if old_drawing:
            db.query(DrawingVersion).filter(DrawingVersion.drawing_id == "mv_draw_002").delete()
            db.delete(old_drawing)
            db.commit()
            print("  已删除旧数据")

        drawing2 = Drawing(**drawing2_data)
        db.add(drawing2)
        db.commit()
        print(f"✓ 创建图纸: {drawing2_data['drawing_no']} - {drawing2_data['name']}")

        # (version_no, change_type, change_reason, days_ago, related_issue)
        versions_data = [
            ("V1.0", "initial", "初始版本，12V输入，5V/3A输出", 30, ""),
            ("V1.1", "fix_issue", "修复输出纹波过大问题，增加输出电容", 25, "ISSUE-2026-003"),
            ("V1.2", "optimization", "优化效率从90%提升到93%，更换功率电感", 15, "ISSUE-2026-008"),
            ("V2.0", "major_change", "重大升级：效率提升到95%，新增过温保护，新增软启动电路", 5, "ISSUE-2026-015"),
        ]

        file_sizes = [1024000, 1152000, 1280000, 1536000]  # 1MB, 1.1MB, 1.2MB, 1.5MB

        for i, vd in enumerate(versions_data):
            ver_no, change_type, change_reason, days_ago, related_issue = vd
            ver_path = f"{DATA_DIR}/mv_draw_002/{ver_no}/power_module_{ver_no.lower()}.pdf"
            create_pdf_mock_file(ver_path, f"Power Module Design {ver_no}",
                               [f"Version {ver_no}",
                                f"Change type: {change_type}",
                                f"Reason: {change_reason}",
                                f"Power efficiency: {85 + i*3}%",
                                f"Output: 5V/{3+i*0.5}A stable",
                                f"Created for: TEST-CTRL-0002"])

            is_latest = (i == len(versions_data) - 1)

            ver = DrawingVersion(
                id=str(uuid.uuid4()),
                drawing_id="mv_draw_002",
                version_no=ver_no,
                file_path=ver_path,
                file_name=f"电源模块设计图_{ver_no}.pdf",
                file_size=file_sizes[i],
                file_format="PDF",
                change_types=change_type,
                change_reason=change_reason,
                related_issue=related_issue,
                uploader_id=engineer_user.id,
                uploaded_at=datetime.now() - timedelta(days=days_ago),
                is_latest=is_latest
            )
            db.add(ver)
            print(f"  ✓ {vd[0]} - PDF文件 ({file_sizes[i]/1024/1024:.1f}MB)" + (" [最新]" if is_latest else ""))

        db.commit()

        # ========== 图纸3：传感器外壳 - 2个版本 (不同格式) ==========
        print("\n--- 创建图纸3：传感器外壳设计 (2个版本，不同格式) ---")

        drawing3_data = {
            "id": "mv_draw_003",
            "drawing_no": "TEST-SENSOR-0001",
            "name": "传感器外壳结构设计",
            "product_id": "prod_005",
            "department_id": "dept_rd1",
            "confidentiality_level": ConfidentialityLevel.C,
            "is_core_part": False,
            "creator_id": designer_user.id,
            "status": DrawingStatus.ACTIVE,
            "review_status": ReviewStatus.PENDING,
            "purpose": "温度传感器外壳设计，IP67防护等级",
            "material": "不锈钢304",
            "dimensions": "φ12mm x 45mm"
        }

        old_drawing = db.query(Drawing).filter(Drawing.id == "mv_draw_003").first()
        if old_drawing:
            db.query(DrawingVersion).filter(DrawingVersion.drawing_id == "mv_draw_003").delete()
            db.delete(old_drawing)
            db.commit()
            print("  已删除旧数据")

        drawing3 = Drawing(**drawing3_data)
        db.add(drawing3)
        db.commit()
        print(f"✓ 创建图纸: {drawing3_data['drawing_no']} - {drawing3_data['name']}")

        # 版本1 - V1.0 (SolidWorks格式，模拟)
        ver1_path = f"{DATA_DIR}/mv_draw_003/V1.0/sensor_housing_v1.sldprt"
        create_text_file(ver1_path,
            "SolidWorks Part File - Sensor Housing V1.0\n"
            "Material: SS304 Stainless Steel\n"
            "Finish: Matte Polish\n"
            "IP67 O-Ring Groove Included\n")

        ver1 = DrawingVersion(
            id=str(uuid.uuid4()),
            drawing_id="mv_draw_003",
            version_no="V1.0",
            file_path=ver1_path,
            file_name="传感器外壳_V1.0.sldprt",
            file_size=3072000,
            file_format="SLDPRT",
            change_types="initial",
            change_reason="初始版本设计",
            uploader_id=designer_user.id,
            uploaded_at=datetime.now() - timedelta(days=20),
            is_latest=False
        )
        db.add(ver1)
        print(f"  ✓ V1.0 - SLDPRT文件 (SolidWorks格式, 3.0MB)")

        # 版本2 - V2.0 (PDF格式) - 优化后的设计
        ver2_path = f"{DATA_DIR}/mv_draw_003/V2.0/sensor_housing_v2.pdf"
        create_pdf_mock_file(ver2_path, "Sensor Housing Design V2.0",
                           ["Final production version V2.0",
                            "Improved thread tolerance",
                            "Added mounting bracket holes",
                            "All dimensions in mm",
                            "Tolerance: +/- 0.05mm",
                            "IP67 confirmed"])

        ver2 = DrawingVersion(
            id=str(uuid.uuid4()),
            drawing_id="mv_draw_003",
            version_no="V2.0",
            file_path=ver2_path,
            file_name="传感器外壳_V2.0.pdf",
            file_size=2048000,
            file_format="PDF",
            change_types="optimization",
            change_reason="优化螺纹公差，增加安装孔位",
            uploader_id=designer_user.id,
            uploaded_at=datetime.now() - timedelta(days=3),
            is_latest=True
        )
        db.add(ver2)
        print(f"  ✓ V2.0 - PDF文件 (最终版, 2.0MB) [最新]")

        db.commit()

        # ========== 图纸4：电机驱动 - 5个版本 (CAD文件) ==========
        print("\n--- 创建图纸4：电机驱动器原理图 (5个版本) ---")

        drawing4_data = {
            "id": "mv_draw_004",
            "drawing_no": "TEST-MOTOR-0001",
            "name": "BLDC电机驱动器原理图",
            "product_id": "prod_003",
            "department_id": "dept_rd1",
            "confidentiality_level": ConfidentialityLevel.A,
            "is_core_part": True,
            "creator_id": engineer_user.id,
            "status": DrawingStatus.ACTIVE,
            "review_status": ReviewStatus.APPROVED,
            "purpose": "直流无刷电机FOC控制驱动器",
            "material": "铝基板PCB",
            "dimensions": "100mm x 80mm",
            "secret_points": "FOC控制算法硬件实现，自研驱动方案"
        }

        old_drawing = db.query(Drawing).filter(Drawing.id == "mv_draw_004").first()
        if old_drawing:
            db.query(DrawingVersion).filter(DrawingVersion.drawing_id == "mv_draw_004").delete()
            db.delete(old_drawing)
            db.commit()
            print("  已删除旧数据")

        drawing4 = Drawing(**drawing4_data)
        db.add(drawing4)
        db.commit()
        print(f"✓ 创建图纸: {drawing4_data['drawing_no']} - {drawing4_data['name']}")

        # (version_no, change_type, change_reason, days_ago, related_issue)
        motor_versions = [
            ("V1.0", "initial", "FOC控制初始版本，6步换向", 50, ""),
            ("V1.1", "fix_issue", "修复换向死区问题，调整PWM频率", 40, "ISSUE-2026-002"),
            ("V1.2", "fix_issue", "修复电流采样偏置问题", 30, "ISSUE-2026-005"),
            ("V2.0", "major_change", "升级到正弦波FOC控制，效率提升15%", 15, "ISSUE-2026-010"),
            ("V2.1", "optimization", "微调PWM时序，优化噪声特性", 5, ""),
        ]

        motor_sizes = [2560000, 2688000, 2816000, 3584000, 2944000]

        for i, (ver_no, change_type, reason, days_ago, related_issue) in enumerate(motor_versions):
            ext = "dwg" if i < 3 else "pdf"
            ver_path = f"{DATA_DIR}/mv_draw_004/{ver_no}/motor_driver_{ver_no.lower()}.{ext}"

            if ext == "dwg":
                create_dwg_mock_file(ver_path, drawing4_data['drawing_no'], ver_no,
                                   f"{reason} - Phase {i+1}")
            else:
                create_pdf_mock_file(ver_path, f"Motor Driver {ver_no}",
                                   [f"Motor Driver Schematic {ver_no}",
                                    f"Change: {reason}",
                                    f"Efficiency: {75 + i*4}%",
                                    f"FOC Algorithm Version {i+1}"])

            ver = DrawingVersion(
                id=str(uuid.uuid4()),
                drawing_id="mv_draw_004",
                version_no=ver_no,
                file_path=ver_path,
                file_name=f"BLDC驱动器原理图_{ver_no}.{ext}",
                file_size=motor_sizes[i],
                file_format=ext.upper(),
                change_types=change_type,
                change_reason=reason,
                related_issue=related_issue,
                uploader_id=engineer_user.id,
                uploaded_at=datetime.now() - timedelta(days=days_ago),
                is_latest=(i == len(motor_versions) - 1)
            )
            db.add(ver)
            status = " [最新]" if ver.is_latest else ""
            print(f"  ✓ {ver_no} - {ext.upper()}文件 ({motor_sizes[i]/1024/1024:.1f}MB){status}")

        db.commit()

        # ========== 图纸5：只有1个版本的图纸 ==========
        print("\n--- 创建图纸5：简单装配图 (1个版本) ---")

        drawing5_data = {
            "id": "mv_draw_005",
            "drawing_no": "TEST-CTRL-0003",
            "name": "控制器装配指导图",
            "product_id": "prod_001",
            "department_id": "dept_rd1",
            "confidentiality_level": ConfidentialityLevel.C,
            "is_core_part": False,
            "creator_id": designer_user.id,
            "status": DrawingStatus.ACTIVE,
            "review_status": ReviewStatus.APPROVED,
            "purpose": "生产线装配指导文件",
            "material": "标准件组装",
            "dimensions": "A3尺寸"
        }

        old_drawing = db.query(Drawing).filter(Drawing.id == "mv_draw_005").first()
        if old_drawing:
            db.query(DrawingVersion).filter(DrawingVersion.drawing_id == "mv_draw_005").delete()
            db.delete(old_drawing)
            db.commit()
            print("  已删除旧数据")

        drawing5 = Drawing(**drawing5_data)
        db.add(drawing5)
        db.commit()
        print(f"✓ 创建图纸: {drawing5_data['drawing_no']} - {drawing5_data['name']}")

        ver_path = f"{DATA_DIR}/mv_draw_005/V1.0/assembly_guide.pdf"
        create_pdf_mock_file(ver_path, "Controller Assembly Guide",
                           ["Step 1: Mount PCB to bottom case",
                            "Step 2: Connect power harness",
                            "Step 3: Install top cover",
                            "Step 4: QC inspection points",
                            "Tightening torque: 0.5N.m"])

        ver5 = DrawingVersion(
            id=str(uuid.uuid4()),
            drawing_id="mv_draw_005",
            version_no="V1.0",
            file_path=ver_path,
            file_name="控制器装配指导图_V1.0.pdf",
            file_size=768000,
            file_format="PDF",
            change_types="initial",
            change_reason="初始版本",
            uploader_id=designer_user.id,
            uploaded_at=datetime.now() - timedelta(days=10),
            is_latest=True
        )
        db.add(ver5)
        print(f"  ✓ V1.0 - PDF文件 (0.7MB) [最新]")

        db.commit()

        print("\n" + "=" * 70)
        print("✓ 多版本测试数据创建完成！")
        print("=" * 70)

        print("\n测试数据摘要:")
        print("-" * 70)
        print(f"  图纸1: TEST-CTRL-0001 控制器主板原理图V3")
        print(f"         版本: V1.0(DWG) → V1.1(PDF) → V2.0(DWG) - 3个版本")
        print(f"         最新: V2.0 DWG格式")
        print()
        print(f"  图纸2: TEST-CTRL-0002 电源模块设计图纸")
        print(f"         版本: V1.0 → V1.1 → V1.2 → V2.0 - 4个版本(全部PDF)")
        print(f"         最新: V2.0 PDF格式")
        print()
        print(f"  图纸3: TEST-SENSOR-0001 传感器外壳结构设计")
        print(f"         版本: V1.0(SLDPRT) → V2.0(PDF) - 2个版本")
        print(f"         最新: V2.0 PDF格式")
        print()
        print(f"  图纸4: TEST-MOTOR-0001 BLDC电机驱动器原理图")
        print(f"         版本: V1.0 → V1.1 → V1.2 → V2.0 → V2.1 - 5个版本")
        print(f"         最新: V2.1 混合格式(DWG/PDF)")
        print()
        print(f"  图纸5: TEST-CTRL-0003 控制器装配指导图")
        print(f"         版本: V1.0 - 1个版本")
        print(f"         最新: V1.0 PDF格式")
        print("-" * 70)
        print("\n文件存储位置: /Volumes/256G/mywork/Blueprint Management System Project/data/drawings/")
        print("\n请用以下账号登录测试：")
        print("  管理员: admin / admin123")
        print("  工程师: lisi_eng / 123456 (上传者，查看自己图纸)")
        print("  设计师: zhangsan / 123456 (上传者，查看自己图纸)")
        print("  CTO: cto / cto123 (查看所有图纸)")

    except Exception as e:
        db.rollback()
        print(f"\n✗ 创建失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    create_multiversion_test_data()
