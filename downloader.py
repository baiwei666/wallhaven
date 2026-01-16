import os
import requests
from concurrent.futures import ThreadPoolExecutor

class Downloader:
    def __init__(self, save_dir, max_workers=5):
        self.save_dir = save_dir
        self.max_workers = max_workers
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)

    def download_image(self, url, filename, progress_callback=None):
        """Download a single image."""
        filepath = os.path.join(self.save_dir, filename)
        if os.path.exists(filepath):
            if progress_callback:
                progress_callback(f"跳过已存在文件: {filename}")
            return True

        try:
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            if progress_callback:
                progress_callback(f"已下载: {filename}")
            return True
        except Exception as e:
            if progress_callback:
                progress_callback(f"下载失败 {filename}: {e}")
            return False

    def batch_download(self, tasks, progress_callback=None):
        """
        tasks: list of (url, filename) tuples
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            full_tasks = [
                executor.submit(self.download_image, url, filename, progress_callback)
                for url, filename in tasks
            ]
            return [task.result() for task in full_tasks]
