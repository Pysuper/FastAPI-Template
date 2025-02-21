#!/usr/bin/env python3
import subprocess
from datetime import datetime
from pathlib import Path


def run_command(cmd):
    """运行命令并返回输出"""
    process = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return process.stdout.strip()


def main():
    # 获取当前时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 创建日志目录
    log_dir = Path("logs/dependency_updates")
    log_dir.mkdir(parents=True, exist_ok=True)

    # 日志文件路径
    log_file = log_dir / f"update_{timestamp}.log"

    with open(log_file, "w") as f:
        # 检查过期依赖
        f.write("=== 检查过期依赖 ===\n")
        outdated = run_command("poetry show --outdated")
        f.write(outdated + "\n\n")

        # 运行安全检查
        f.write("=== 运行安全检查 ===\n")
        safety_check = run_command("poetry run safety check")
        f.write(safety_check + "\n\n")

        # 运行 Bandit 安全扫描
        f.write("=== 运行 Bandit 安全扫描 ===\n")
        bandit_scan = run_command("poetry run bandit -r app/")
        f.write(bandit_scan + "\n\n")

        # 更新依赖
        f.write("=== 更新依赖 ===\n")
        update = run_command("poetry update")
        f.write(update + "\n\n")

        # 导出requirements.txt
        f.write("=== 导出requirements.txt ===\n")
        export_main = run_command("poetry export -f requirements.txt --without-hashes > requirements.txt")
        export_dev = run_command("poetry export -f requirements.txt --without-hashes --with dev > requirements-dev.txt")
        f.write("已导出 requirements.txt 和 requirements-dev.txt\n")

        # 运行测试
        f.write("=== 运行测试 ===\n")
        test_result = run_command("poetry run pytest")
        f.write(test_result + "\n")

    print(f"依赖更新完成，日志已保存到: {log_file}")


if __name__ == "__main__":
    main()
