"""
版本管理和自動更新模組
提供版本檢查、下載更新、啟動替換腳本
"""

import os
import sys
import tempfile

# 從 version.py 獲取版本號
try:
    from version import get_version
    CURRENT_VERSION = get_version()
except ImportError:
    # 如果無法導入，使用默認值
    CURRENT_VERSION = "1.0.8"

# GitHub Release API
GITHUB_API_URL = "https://api.github.com/repos/asd23353934/skill_tracker/releases/latest"

# 嘗試導入 requests
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    print("⚠️ 未安裝 requests 模組，自動更新功能已停用")
    print("   若要啟用自動更新，請執行: pip install requests")

# 嘗試導入 packaging
try:
    from packaging import version as pkg_version
    HAS_PACKAGING = True
except ImportError:
    HAS_PACKAGING = False


class Updater:
    """自動更新檢查器與下載器"""

    def __init__(self):
        self.current_version = CURRENT_VERSION
        self.latest_version = None
        self.download_url = None
        self.update_available = False

    def check_for_updates(self):
        """檢查是否有新版本

        Returns:
            dict: {
                'available': bool,
                'current': str,
                'latest': str,
                'download_url': str,
                'release_notes': str
            }
        """
        # 檢查依賴
        if not HAS_REQUESTS:
            return {
                'available': False,
                'current': self.current_version,
                'error': 'requests module not installed'
            }

        try:
            response = requests.get(GITHUB_API_URL, timeout=5)
            response.raise_for_status()

            release_data = response.json()

            # 獲取最新版本號（移除 'v' 前綴）
            latest_tag = release_data.get('tag_name', '').lstrip('v')

            # 比較版本
            if self._compare_versions(latest_tag, self.current_version):
                self.update_available = True
                self.latest_version = latest_tag

                # 獲取下載連結（優先 .exe，其次 .7z / .zip / .tar.gz）
                assets = release_data.get('assets', [])
                exe_url = None
                archive_url = None

                for asset in assets:
                    name = asset['name'].lower()
                    url = asset['browser_download_url']
                    if name.endswith('.exe'):
                        exe_url = url
                    elif name.endswith(('.7z', '.zip', '.tar.gz')):
                        archive_url = url

                # 備用：若 assets 未列出，依已知命名規則組合 URL
                fallback_url = (
                    f"https://github.com/asd23353934/skill_tracker"
                    f"/releases/download/v{latest_tag}"
                    f"/skill_tracker_v{latest_tag}.zip"
                )
                self.download_url = exe_url or archive_url or fallback_url

                return {
                    'available': True,
                    'current': self.current_version,
                    'latest': self.latest_version,
                    'download_url': self.download_url,
                    'release_notes': release_data.get('body', '')
                }

            return {
                'available': False,
                'current': self.current_version,
                'latest': self.current_version
            }

        except Exception as e:
            print(f"⚠️ 檢查更新失敗: {e}")
            return {
                'available': False,
                'current': self.current_version,
                'error': str(e)
            }

    def download_update(self, url, dest_path, progress_callback=None):
        """下載更新檔案

        Args:
            url: 下載連結
            dest_path: 儲存路徑
            progress_callback: 進度回調 (downloaded_bytes, total_bytes)

        Returns:
            bool: 下載是否成功
        """
        if not HAS_REQUESTS:
            return False

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            with open(dest_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)

            return True

        except Exception as e:
            print(f"⚠️ 下載更新失敗: {e}")
            # 清理不完整的下載
            try:
                if os.path.exists(dest_path):
                    os.remove(dest_path)
            except Exception:
                pass
            return False

    def get_update_temp_path(self):
        """取得更新暫存檔案路徑

        Returns:
            暫存檔案的完整路徑
        """
        temp_dir = tempfile.gettempdir()
        if self.download_url:
            filename = os.path.basename(self.download_url)
        else:
            filename = "skill_tracker_update.7z"
        return os.path.join(temp_dir, filename)

    def get_launcher_path(self):
        """取得更新啟動腳本路徑

        Returns:
            update_launcher.bat 的完整路徑
        """
        from src.ui.helpers import resource_path
        return resource_path("update_launcher.bat")

    def _compare_versions(self, latest, current):
        """比較版本號

        Args:
            latest: 最新版本
            current: 當前版本

        Returns:
            bool: 如果最新版本更高返回 True
        """
        if HAS_PACKAGING:
            try:
                return pkg_version.parse(latest) > pkg_version.parse(current)
            except Exception:
                pass

        # 簡單的數值比較（fallback）
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            return latest_parts > current_parts
        except Exception:
            return False

    def open_download_page(self):
        """打開下載頁面"""
        import webbrowser
        if self.download_url:
            webbrowser.open(self.download_url)
        else:
            webbrowser.open(
                "https://github.com/asd23353934/skill_tracker/releases/latest"
            )
