from main_gui import MainWindow
from PyQt6.QtWidgets import QApplication
import sys

def main():
    app = QApplication(sys.argv)
    
    # 设置一些全局样式（可选）
    app.setStyle("Fusion")
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
