#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L-SHADE算法测试脚本
"""

def test_l_shade_import():
    """测试L-SHADE模块导入"""
    try:
        import l_shade_well_trajectory
        print("✓ L-SHADE模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ L-SHADE模块导入失败: {e}")
        return False

def test_l_shade_class():
    """测试L-SHADE类创建"""
    try:
        from l_shade_well_trajectory import LSHADEWellTrajectoryOptimizer
        print("✓ LSHADEWellTrajectoryOptimizer类导入成功")
        return True
    except ImportError as e:
        print(f"✗ LSHADEWellTrajectoryOptimizer类导入失败: {e}")
        return False

def test_l_shade_core():
    """测试L-SHADE核心模块"""
    try:
        from l_shade_core import LSHADE
        print("✓ LSHADE核心类导入成功")
        return True
    except ImportError as e:
        print(f"✗ LSHADE核心类导入失败: {e}")
        return False

def test_minimal_interface():
    """测试简化接口"""
    try:
        from minimal_l_shade import optimize_well_trajectory
        print("✓ minimal_l_shade模块导入成功")
        return True
    except ImportError as e:
        print(f"✗ minimal_l_shade模块导入失败: {e}")
        return False

def main():
    """主测试函数"""
    print("L-SHADE算法实现测试")
    print("=" * 40)
    
    tests = [
        ("L-SHADE模块导入", test_l_shade_import),
        ("L-SHADE类导入", test_l_shade_class),
        ("L-SHADE核心模块导入", test_l_shade_core),
        ("简化接口导入", test_minimal_interface),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n测试: {test_name}")
        if test_func():
            passed += 1
    
    print(f"\n测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("✓ 所有测试通过！L-SHADE实现正常")
    else:
        print("✗ 部分测试失败，请检查实现")

if __name__ == "__main__":
    main()

