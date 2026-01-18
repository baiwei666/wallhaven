import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QLineEdit, QPushButton, QTextEdit, QFileDialog, 
                             QCheckBox, QComboBox, QGroupBox, QProgressBar, QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings
from wallhaven_api import WallhavenAPI
from downloader import Downloader

class WorkerThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()
    
    def __init__(self, api_key, save_dir, keyword, categories, purity, sorting, resolutions, ratios, atleast, pages, max_workers, min_favs=0, min_views=0):
        super().__init__()
        self.api_key = api_key
        self.save_dir = save_dir
        self.keyword = keyword
        self.categories = categories
        self.purity = purity
        self.sorting = sorting
        self.resolutions = resolutions
        self.ratios = ratios
        self.atleast = atleast
        self.pages = pages
        self.max_workers = max_workers
        self.min_favs = min_favs
        self.min_views = min_views
        self.is_running = True

    def run(self):
        import time
        api = WallhavenAPI(api_key=self.api_key)
        downloader = Downloader(self.save_dir, max_workers=self.max_workers)
        
        total_downloaded = 0
        page = 1
        consecutive_empty_pages = 0  # Track consecutive empty pages
        max_consecutive_empty = 3    # Stop after 3 consecutive truly empty pages
        retry_count = 0
        max_retries = 3
        
        while page <= self.pages:
            if not self.is_running:
                break
                
            self.progress_signal.emit(f"正在搜索第 {page} 页...")
            data = api.search(q=self.keyword, categories=self.categories, purity=self.purity, 
                              sorting=self.sorting, resolutions=self.resolutions, ratios=self.ratios, 
                              atleast=self.atleast, page=page)
            
            # Handle API errors with retry
            if not data or 'data' not in data:
                retry_count += 1
                if retry_count <= max_retries:
                    self.progress_signal.emit(f"第 {page} 页请求失败，{2*retry_count}秒后重试 ({retry_count}/{max_retries})...")
                    time.sleep(2 * retry_count)  # Exponential backoff
                    continue
                else:
                    self.progress_signal.emit(f"第 {page} 页多次请求失败，跳过此页继续...")
                    retry_count = 0
                    page += 1
                    continue
            
            retry_count = 0  # Reset retry count on success
            wallpapers = data['data']
            
            # Check for truly empty results (end of search)
            if not wallpapers:
                consecutive_empty_pages += 1
                if consecutive_empty_pages >= max_consecutive_empty:
                    self.progress_signal.emit(f"连续 {max_consecutive_empty} 页无结果，搜索结束。")
                    break
                self.progress_signal.emit(f"第 {page} 页无结果，继续搜索... ({consecutive_empty_pages}/{max_consecutive_empty})")
                page += 1
                time.sleep(0.5)  # Small delay to avoid rate limiting
                continue
            
            consecutive_empty_pages = 0  # Reset on non-empty page
            
            # Client-side filtering by favorites and views
            filtered_wallpapers = []
            for wp in wallpapers:
                if self.min_favs > 0 and wp.get('favorites', 0) < self.min_favs:
                    continue
                if self.min_views > 0 and wp.get('views', 0) < self.min_views:
                    continue
                filtered_wallpapers.append(wp)
            
            filtered_count = len(wallpapers) - len(filtered_wallpapers)
            if filtered_count > 0:
                self.progress_signal.emit(f"第 {page} 页过滤了 {filtered_count} 张不符合条件的图片。")
            
            if not filtered_wallpapers:
                self.progress_signal.emit(f"第 {page} 页没有符合条件的图片，继续下一页...")
                page += 1
                time.sleep(0.3)  # Small delay
                continue
                
            tasks = []
            skipped_count = 0
            for wp in filtered_wallpapers:
                url = wp.get('path')
                wp_id = wp.get('id')
                ext = os.path.splitext(url)[1]
                filename = f"wallhaven-{wp_id}{ext}"
                filepath = os.path.join(self.save_dir, filename)
                
                # Deduplication check
                if os.path.exists(filepath):
                    skipped_count += 1
                    continue
                    
                tasks.append((url, filename))
            
            if skipped_count > 0:
                self.progress_signal.emit(f"第 {page} 页自动跳过 {skipped_count} 张已存在图片。")

            if not tasks:
                self.progress_signal.emit(f"第 {page} 页没有新图片需要下载。")
                page += 1
                continue

            self.progress_signal.emit(f"第 {page} 页找到 {len(tasks)} 张符合条件的新壁纸，准备下载...")
            
            def log_progress(msg):
                self.progress_signal.emit(msg)
                
            results = downloader.batch_download(tasks, progress_callback=log_progress)
            success_count = sum(results)
            total_downloaded += success_count
            self.progress_signal.emit(f"第 {page} 页下载完成。成功: {success_count}, 失败/跳过: {len(results) - success_count}")
            
            page += 1
            time.sleep(0.3)  # Rate limiting protection

        self.progress_signal.emit(f"任务结束。共下载 {total_downloaded} 张图片。")
        self.finished_signal.emit()

    def stop(self):
        self.is_running = False

class MainWindow(QMainWindow):
    def resource_path(self, relative_path):
        """ Get absolute path to resource, works for dev and for PyInstaller """
        try:
            # PyInstaller creates a temp folder and stores path in _MEIPASS
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")

        return os.path.join(base_path, relative_path)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wallhaven 壁纸下载器")
        self.resize(800, 600)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Load Stylesheet
        try:
            style_path = self.resource_path("style.qss")
            with open(style_path, "r") as f:
                self.setStyleSheet(f.read())
        except Exception:
            pass # Fail silently if no style file

        self.settings = QSettings("WallhavenDownloader", "Settings")
        
        # --- Settings Area ---
        settings_group = QGroupBox("设置")
        settings_layout = QVBoxLayout()
        
        # API Key
        api_layout = QHBoxLayout()
        api_layout.setSpacing(10)
        api_layout.addWidget(QLabel("API Key (可选):"))
        self.api_input = QLineEdit()
        self.api_input.setPlaceholderText("留空则使用匿名访问（限制更多）")
        self.api_input.setText(self.settings.value("api_key", ""))
        api_layout.addWidget(self.api_input)
        settings_layout.addLayout(api_layout)
        
        # Save Directory
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(10)
        dir_layout.addWidget(QLabel("保存路径:"))
        default_dir = os.path.join(os.getcwd(), "downloads")
        self.dir_input = QLineEdit(self.settings.value("save_dir", default_dir))
        dir_layout.addWidget(self.dir_input)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_btn.clicked.connect(self.browse_directory)
        dir_layout.addWidget(self.browse_btn)
        settings_layout.addLayout(dir_layout)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # --- Search & Filter Area ---
        filter_group = QGroupBox("搜索与筛选")
        filter_layout = QVBoxLayout()
        
        # Keyword
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("关键词:"))
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("例如: anime, landscape, id:5")
        search_layout.addWidget(self.keyword_input)
        filter_layout.addLayout(search_layout)
        
        # Options Line 1
        options_layout = QHBoxLayout()
        
        # Categories
        self.cat_general = QCheckBox("General")
        self.cat_general.setChecked(True)
        self.cat_anime = QCheckBox("Anime")
        self.cat_anime.setChecked(True)
        self.cat_people = QCheckBox("People")
        self.cat_people.setChecked(False) # Default off for safety/preference
        options_layout.addWidget(QLabel("分类:"))
        options_layout.addWidget(self.cat_general)
        options_layout.addWidget(self.cat_anime)
        options_layout.addWidget(self.cat_people)
        
        options_layout.addSpacing(20)
        
        # Purity
        self.purity_sfw = QCheckBox("SFW")
        self.purity_sfw.setChecked(True)
        self.purity_sketchy = QCheckBox("Sketchy")
        self.purity_nsfw = QCheckBox("NSFW") # Need API Key usually
        options_layout.addWidget(QLabel("分级:"))
        options_layout.addWidget(self.purity_sfw)
        options_layout.addWidget(self.purity_sketchy)
        options_layout.addWidget(self.purity_nsfw)
        
        filter_layout.addLayout(options_layout)
        
        # Options Line 2
        options_layout2 = QHBoxLayout()
        
        # Sorting
        options_layout2.addWidget(QLabel("排序:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["date_added", "relevance", "random", "views", "favorites", "toplist"])
        options_layout2.addWidget(self.sort_combo)
        
        options_layout2.addSpacing(20)

        # Resolution Mode & Value
        res_layout = QVBoxLayout()
        res_label_layout = QHBoxLayout()
        res_label_layout.addWidget(QLabel("分辨率:"))
        self.res_mode_combo = QComboBox()
        self.res_mode_combo.addItem("Exact (精确)", "exact")
        self.res_mode_combo.addItem("At Least (至少)", "atleast")
        res_label_layout.addWidget(self.res_mode_combo)
        res_layout.addLayout(res_label_layout)

        self.res_combo = QComboBox()
        self.res_combo.addItem("Any", None)
        self.res_combo.addItem("1920x1080 (1080p)", "1920x1080")
        self.res_combo.addItem("2560x1440 (2K)", "2560x1440")
        self.res_combo.addItem("3840x2160 (4K)", "3840x2160")
        self.res_combo.addItem("5120x2880 (5K)", "5120x2880")
        self.res_combo.addItem("7680x4320 (8K)", "7680x4320")
        self.res_combo.addItem("Ultra Wide (3440...)", "3440x1440,2560x1080")
        res_layout.addWidget(self.res_combo)
        
        options_layout2.addLayout(res_layout)

        # Ratio
        ratio_layout = QVBoxLayout()
        ratio_layout.addWidget(QLabel("比例:"))
        self.ratio_combo = QComboBox()
        self.ratio_combo.addItem("Any", None)
        self.ratio_combo.addItem("16x9", "16x9")
        self.ratio_combo.addItem("21x9", "21x9")
        self.ratio_combo.addItem("16x10", "16x10")
        self.ratio_combo.addItem("4x3", "4x3")
        self.ratio_combo.addItem("Portrait", "9x16,10x16")
        options_layout2.addWidget(self.ratio_combo)
        
        filter_layout.addLayout(options_layout2)
        
        # Options Line 3 (New Filters & Pages/Threads)
        options_layout3 = QHBoxLayout()
        
        # Min Favorites
        options_layout3.addWidget(QLabel("最少点赞:"))
        self.min_favs_spin = QSpinBox()
        self.min_favs_spin.setRange(0, 1000000)
        self.min_favs_spin.setValue(0)
        self.min_favs_spin.setSingleStep(10)
        options_layout3.addWidget(self.min_favs_spin)

        options_layout3.addSpacing(10)

        # Min Views
        options_layout3.addWidget(QLabel("最少观看:"))
        self.min_views_spin = QSpinBox()
        self.min_views_spin.setRange(0, 100000000)
        self.min_views_spin.setValue(0)
        self.min_views_spin.setSingleStep(1000)
        options_layout3.addWidget(self.min_views_spin)

        options_layout3.addSpacing(20)

        # Pages
        pages_layout = QVBoxLayout()
        pages_label_layout = QHBoxLayout()
        pages_label_layout.addWidget(QLabel("页数:"))
        self.all_pages_check = QCheckBox("全部")
        self.all_pages_check.setToolTip("下载该搜索条件下的所有页")
        self.all_pages_check.toggled.connect(self.toggle_pages_spin)
        pages_label_layout.addWidget(self.all_pages_check)
        pages_layout.addLayout(pages_label_layout)
        
        self.page_spin = QSpinBox()
        self.page_spin.setRange(1, 99999)
        self.page_spin.setValue(1)
        pages_layout.addWidget(self.page_spin)
        
        options_layout3.addLayout(pages_layout)

        # Threads
        options_layout3.addWidget(QLabel("下载线程:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 20)
        self.thread_spin.setValue(5)
        options_layout3.addWidget(self.thread_spin)

        filter_layout.addLayout(options_layout3)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # --- Action & Log Area ---
        self.start_btn = QPushButton("开始下载")
        self.start_btn.setObjectName("PrimaryButton")
        self.start_btn.setMinimumHeight(50)
        self.start_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_btn.clicked.connect(self.start_download)
        layout.addWidget(self.start_btn)
        
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(self.log_area)
        
        self.worker = None

    def toggle_pages_spin(self, checked):
        self.page_spin.setDisabled(checked)

    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "选择保存路径")
        if directory:
            self.dir_input.setText(directory)

    def log(self, message):
        self.log_area.append(message)
        # Scroll to bottom
        scrollbar = self.log_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def start_download(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            self.log("任务已停止。")
            self.start_btn.setText("开始下载")
            return

        api_key = self.api_input.text().strip()
        save_dir = self.dir_input.text().strip()
        keyword = self.keyword_input.text().strip()
        
        # Remove appending to keyword, pass explicitly
        min_favs = self.min_favs_spin.value()
        min_views = self.min_views_spin.value()
        
        # Construct categories string "100" etc
        c_gen = "1" if self.cat_general.isChecked() else "0"
        c_ani = "1" if self.cat_anime.isChecked() else "0"
        c_peo = "1" if self.cat_people.isChecked() else "0"
        categories = f"{c_gen}{c_ani}{c_peo}"
        
        # Construct purity string
        p_sfw = "1" if self.purity_sfw.isChecked() else "0"
        p_sky = "1" if self.purity_sketchy.isChecked() else "0"
        p_nsf = "1" if self.purity_nsfw.isChecked() else "0"
        purity = f"{p_sfw}{p_sky}{p_nsf}"
        
        sorting = self.sort_combo.currentText()
        
        res_val = self.res_combo.currentData()
        res_mode = self.res_mode_combo.currentData()
        
        resolutions = None
        atleast = None
        
        if res_val:
            if res_mode == "atleast":
                atleast = res_val
            else:
                resolutions = res_val

        ratios = self.ratio_combo.currentData()
        
        if self.all_pages_check.isChecked():
            pages = 999999 # Effective infinity for this script
        else:
            pages = self.page_spin.value()
            
        max_workers = self.thread_spin.value()
        
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                QMessageBox.critical(self, "错误", f"无法创建保存目录: {e}")
                return

        self.start_btn.setText("停止下载")
        self.log(f"任务: '{keyword}' | 排序:{sorting} | 分辨率:{res_val}({res_mode}) | 比例:{ratios} | 页数:{'ALL' if pages > 100000 else pages} | 过滤: Fav>={min_favs}, View>={min_views}")
        
        self.worker = WorkerThread(api_key, save_dir, keyword, categories, purity, sorting, resolutions, ratios, atleast, pages, max_workers, min_favs, min_views)
        self.worker.progress_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def on_finished(self):
        self.start_btn.setText("开始下载")
        QMessageBox.information(self, "完成", "所有任务已完成！")

    def closeEvent(self, event):
        self.settings.setValue("api_key", self.api_input.text())
        self.settings.setValue("save_dir", self.dir_input.text())
        super().closeEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
