import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

BEIJING_TZ = timezone(timedelta(hours=8))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "auto_update.log")

def log(msg: str):
    timestamp = datetime.now(BEIJING_TZ).strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass

def run_cmd(cmd, cwd=BASE_DIR, check=True):
    log(f"执行命令: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, encoding="utf-8", shell=isinstance(cmd, str))
    if res.stdout:
        for out_line in res.stdout.strip().splitlines()[-5:]:
            log(f"  [stdout] {out_line}")
    if res.stderr:
        for err_line in res.stderr.strip().splitlines()[-5:]:
            log(f"  [stderr] {err_line}")
    if check and res.returncode != 0:
        raise RuntimeError(f"命令执行失败，退出码: {res.returncode}")
    return res

def main():
    log("=== 开始检查/执行每日番茄男频榜单自动更新 ===")
    
    # 1. 同步最新代码
    try:
        run_cmd(["git", "pull", "--rebase", "origin", "main"], check=False)
    except Exception as e:
        log(f"拉取远程更新警告: {e}")

    # 2. 检查今天是否完整
    today = datetime.now(BEIJING_TZ).strftime("%Y%m%d")
    state_file = os.path.join(BASE_DIR, "data", "male", f"task_state_{today}.json")
    is_complete = False
    if os.path.exists(state_file):
        try:
            import json
            with open(state_file, "r", encoding="utf-8") as f:
                completed = json.load(f).get("completed", [])
                if len(completed) >= 19:
                    is_complete = True
        except Exception:
            pass

    if is_complete:
        log(f"今日 ({today}) 男频 19 个分类数据已全部就绪，无需重复抓取。")
        return

    # 3. 抓取数据
    log("开始运行抓取爬虫...")
    run_cmd([sys.executable, "scrape_fanqie_ranks.py"])

    # 4. 构建数据
    log("构建最新榜单与聚合数据...")
    run_cmd([sys.executable, os.path.join("scripts", "build_latest.py"), "--channel", "male"])

    # 5. Git 提交并推送
    log("提交并推送新数据到 GitHub...")
    run_cmd(["git", "add", "data/", "api/"])
    diff_res = subprocess.run(["git", "diff", "--staged", "--quiet"], cwd=BASE_DIR)
    if diff_res.returncode != 0:
        run_cmd(["git", "commit", "-m", f"[Auto] Update Fanqie male ranks ({today})"])
        run_cmd(["git", "push", "origin", "main"])
        log("✅ 今日更新并推送到远程仓库成功！")
    else:
        log("无新变更需要提交。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"❌ 自动更新发生异常: {e}")
        sys.exit(1)
