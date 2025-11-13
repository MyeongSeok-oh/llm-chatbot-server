#!/usr/bin/env python3
"""
자동 Git 동기화 스크립트
파일 변경을 감지하고 자동으로 GitHub에 커밋/푸시합니다.
"""

import os
import sys
import time
import subprocess
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class GitAutoSync(FileSystemEventHandler):
    """파일 변경을 감지하고 자동으로 Git 커밋/푸시"""

    def __init__(self, repo_path, branch="claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T",
                 ignore_patterns=None, delay=5):
        self.repo_path = Path(repo_path)
        self.branch = branch
        self.delay = delay  # 변경 후 대기 시간 (초)
        self.last_sync_time = 0
        self.pending_changes = False

        # 무시할 패턴
        self.ignore_patterns = ignore_patterns or [
            '.git',
            '__pycache__',
            '*.pyc',
            '.env',
            'chroma_db',
            'chat_history',
            'node_modules',
            '.DS_Store',
            '*.log'
        ]

    def should_ignore(self, path):
        """특정 파일/디렉토리를 무시해야 하는지 확인"""
        path_str = str(path)
        for pattern in self.ignore_patterns:
            if pattern in path_str:
                return True
        return False

    def run_git_command(self, command):
        """Git 명령 실행"""
        try:
            result = subprocess.run(
                command,
                cwd=self.repo_path,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            print("⏱️  Git 명령 타임아웃")
            return False, "", "Timeout"
        except Exception as e:
            print(f"❌ Git 명령 실행 오류: {e}")
            return False, "", str(e)

    def sync_to_github(self):
        """변경사항을 GitHub에 동기화"""
        current_time = time.time()

        # 너무 자주 동기화하지 않도록 제한
        if current_time - self.last_sync_time < self.delay:
            return

        print("\n" + "="*60)
        print(f"🔄 Git 동기화 시작... [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
        print("="*60)

        # 1. 현재 상태 확인
        success, stdout, stderr = self.run_git_command("git status --porcelain")
        if not success:
            print(f"❌ Git 상태 확인 실패: {stderr}")
            return

        if not stdout.strip():
            print("✅ 변경사항 없음")
            self.pending_changes = False
            return

        print(f"📝 변경된 파일:\n{stdout}")

        # 2. 변경사항 스테이징
        print("📦 변경사항 스테이징 중...")
        success, _, stderr = self.run_git_command("git add -A")
        if not success:
            print(f"❌ 스테이징 실패: {stderr}")
            return

        # 3. 커밋
        commit_message = f"Auto-sync: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        print(f"💾 커밋 중: {commit_message}")
        success, _, stderr = self.run_git_command(f'git commit -m "{commit_message}"')
        if not success:
            if "nothing to commit" in stderr:
                print("✅ 커밋할 내용 없음")
            else:
                print(f"❌ 커밋 실패: {stderr}")
            return

        # 4. 푸시 (재시도 로직 포함)
        print(f"🚀 GitHub에 푸시 중 (브랜치: {self.branch})...")
        max_retries = 4
        retry_delays = [2, 4, 8, 16]  # 지수 백오프

        for attempt in range(max_retries):
            success, stdout, stderr = self.run_git_command(f"git push -u origin {self.branch}")

            if success:
                print("✅ GitHub에 성공적으로 푸시됨!")
                self.last_sync_time = current_time
                self.pending_changes = False
                return

            if attempt < max_retries - 1:
                delay = retry_delays[attempt]
                print(f"⚠️  푸시 실패 (시도 {attempt + 1}/{max_retries}): {stderr}")
                print(f"⏳ {delay}초 후 재시도...")
                time.sleep(delay)
            else:
                print(f"❌ 푸시 최종 실패: {stderr}")

        print("="*60 + "\n")

    def on_modified(self, event):
        """파일 수정 시 호출"""
        if event.is_directory or self.should_ignore(event.src_path):
            return

        print(f"📝 파일 변경 감지: {event.src_path}")
        self.pending_changes = True

    def on_created(self, event):
        """파일 생성 시 호출"""
        if event.is_directory or self.should_ignore(event.src_path):
            return

        print(f"➕ 파일 생성 감지: {event.src_path}")
        self.pending_changes = True

    def on_deleted(self, event):
        """파일 삭제 시 호출"""
        if event.is_directory or self.should_ignore(event.src_path):
            return

        print(f"🗑️  파일 삭제 감지: {event.src_path}")
        self.pending_changes = True


def check_git_repo(path):
    """Git 저장소인지 확인"""
    git_dir = Path(path) / '.git'
    if not git_dir.exists():
        print(f"❌ Git 저장소가 아닙니다: {path}")
        return False
    return True


def check_git_branch(path, branch):
    """현재 브랜치 확인 및 생성"""
    try:
        # 현재 브랜치 확인
        result = subprocess.run(
            "git branch --show-current",
            cwd=path,
            shell=True,
            capture_output=True,
            text=True
        )
        current_branch = result.stdout.strip()

        if current_branch != branch:
            print(f"⚠️  현재 브랜치: {current_branch}")
            print(f"🔀 {branch} 브랜치로 전환 중...")

            # 브랜치가 존재하는지 확인
            result = subprocess.run(
                f"git rev-parse --verify {branch}",
                cwd=path,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                # 브랜치가 없으면 생성
                print(f"🌱 새 브랜치 생성: {branch}")
                subprocess.run(f"git checkout -b {branch}", cwd=path, shell=True)
            else:
                # 브랜치가 있으면 전환
                subprocess.run(f"git checkout {branch}", cwd=path, shell=True)

        print(f"✅ 브랜치 확인: {branch}")
        return True
    except Exception as e:
        print(f"❌ 브랜치 확인 실패: {e}")
        return False


def main():
    """메인 함수"""
    print("""
╔═══════════════════════════════════════════════════════════╗
║          🤖 Git 자동 동기화 스크립트                      ║
║          파일 변경 시 자동으로 GitHub에 푸시합니다         ║
╚═══════════════════════════════════════════════════════════╝
""")

    # 설정
    repo_path = os.getcwd()
    branch = "claude/local-integration-setup-011CV5X2DN6gjH1SzxsWbo7T"
    delay = 5  # 변경 후 대기 시간 (초)

    # Git 저장소 확인
    if not check_git_repo(repo_path):
        sys.exit(1)

    # 브랜치 확인
    if not check_git_branch(repo_path, branch):
        sys.exit(1)

    print(f"\n📂 감시 경로: {repo_path}")
    print(f"🌿 브랜치: {branch}")
    print(f"⏱️  동기화 딜레이: {delay}초")
    print(f"\n👀 파일 변경 감시 시작... (Ctrl+C로 종료)\n")

    # 이벤트 핸들러 및 옵저버 설정
    event_handler = GitAutoSync(repo_path, branch=branch, delay=delay)
    observer = Observer()
    observer.schedule(event_handler, repo_path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(delay)
            # 대기 중인 변경사항이 있으면 동기화
            if event_handler.pending_changes:
                event_handler.sync_to_github()
    except KeyboardInterrupt:
        print("\n\n⏹️  자동 동기화 중지 중...")
        observer.stop()

    observer.join()
    print("✅ 자동 동기화 종료")


if __name__ == "__main__":
    main()
