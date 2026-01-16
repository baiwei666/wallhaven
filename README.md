# Wallhaven 壁纸下载器

一个基于 Python 和 PyQt6 构建的强大且现代的桌面 GUI 应用程序，用于从 [Wallhaven.cc](https://wallhaven.cc) 搜索和下载高质量壁纸。

![Wallhaven Downloader](https://via.placeholder.com/800x600?text=Wallhaven+Downloader+GUI)

## 🌟 主要功能

### 🔍 高级搜索与筛选
- **关键词搜索**：支持按标签、关键词或图片 ID（例如 `id:5`）进行搜索。
- **分类筛选**：可筛选 General（一般）、Anime（动漫）和 People（人物）分类。
- **分级筛选**：支持切换 SFW（全年龄）、Sketchy（需谨慎）和 NSFW（限制级）内容（NSFW 内容通常需要 API Key）。
- **排序方式**：支持按添加日期、相关度、随机、浏览量、收藏量或排行榜进行排序。

### 📐 精确下载控制
- **分辨率控制**：
  - 标准预设：1080p, 2K, 4K, 5K, 8K, Ultra Wide（超宽屏）。
  - "At Least"（至少）模式：查找尺寸达到或超过指定分辨率的壁纸。
  - 精确匹配模式：查找尺寸完全符合指定分辨率的壁纸。
- **纵横比**：支持筛选 16:9, 21:9, 16:10, 4:3 以及 Portrait（竖屏）比例。

### ⚡ 性能与易用性
- **多线程下载**：支持批量下载，线程数可配置，大幅提升下载速度。
- **智能校验**：自动检测并跳过已下载的文件，避免重复下载。
- **实时日志**：界面实时显示详细的进度日志、搜索结果统计和下载状态。
- **设置记忆**：自动保存您的 API Key 和下载目录设置，无需每次重新输入。

## 🛠️ 安装指南

### 前置要求
- Python 3.8 或更高版本

### 安装依赖
请使用 pip 安装所需的 Python 库：

```bash
pip install requests PyQt6
```

## 🚀 使用方法

1. **克隆仓库**：
   ```bash
   git clone https://github.com/yourusername/wallhaven-downloader.git
   cd wallhaven-downloader
   ```

2. **运行应用程序**：
   ```bash
   python main_gui.py
   ```

3. **配置与下载**：
   - （可选）在设置区域输入您的 **Wallhaven API Key** 以解除速率限制或访问 NSFW 内容。
   - 点击“浏览”选择您的 **保存目录**。
   - 设置您想要的筛选条件（如分类、分辨率、排序等）。
   - 点击 **开始下载** 按钮。

## 📝 配置说明

- **API Key**：虽然该项为可选，但配置 API Key 后可以获得更高的 API 请求限额，并且如果您的 Wallhaven 账号开启了 NSFW 权限，该工具也能下载相关内容。
- **下载线程**：您可以根据网络状况在界面上调整同时下载的线程数量（默认设置为 5）。

## 📄 许可证

本项目采用 MIT 许可证 - 详情请参阅 [LICENSE](LICENSE) 文件。

---
*免责声明：本工具与 Wallhaven.cc 官方无关。使用时请遵守 Wallhaven 的 API 使用政策。*
