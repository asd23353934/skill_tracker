"""
版本管理和自動更新模組
"""

import os
import sys

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
    """自動更新檢查器"""
    
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
                
                # 獲取下載連結
                assets = release_data.get('assets', [])
                for asset in assets:
                    if asset['name'].endswith('.tar.gz') or asset['name'].endswith('.zip'):
                        self.download_url = asset['browser_download_url']
                        break
                
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
            except:
                pass
        
        # 簡單的字符串比較（fallback）
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            return latest_parts > current_parts
        except:
            return False
    
    def open_download_page(self):
        """打開下載頁面"""
        if self.download_url:
            import webbrowser
            webbrowser.open(self.download_url)
        else:
            # 打開 releases 頁面
            import webbrowser
            webbrowser.open("https://github.com/asd23353934/skill_tracker/releases/latest")
