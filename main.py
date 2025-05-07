import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                           QWidget, QVBoxLayout, QPushButton, QFileDialog,
                           QLabel, QMessageBox, QCheckBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer
import win32clipboard
from PIL import Image
import io

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ScreenshotApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('スクリーンショット保存')
        self.setGeometry(100, 100, 400, 250)
        
        # 設定ファイルのパス
        self.config_file = 'screenshot_config.json'
        
        # 設定の読み込み
        self.load_config()
        
        # GUIの設定
        self.setup_ui()
        
        # システムトレイアイコンの設定
        self.setup_tray()
        
        # 自動保存用のタイマー
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.check_clipboard)
        self.last_clipboard_data = None
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # 保存先表示ラベル
        self.path_label = QLabel(f'保存先: {self.save_path}')
        layout.addWidget(self.path_label)
        
        # 保存先変更ボタン
        change_path_btn = QPushButton('保存先を変更')
        change_path_btn.clicked.connect(self.change_save_path)
        layout.addWidget(change_path_btn)
        
        # 初期値に戻すボタン
        reset_btn = QPushButton('初期値に戻す')
        reset_btn.clicked.connect(self.reset_path)
        layout.addWidget(reset_btn)
        
        # 自動保存チェックボックス
        self.auto_save_checkbox = QCheckBox('自動保存を有効にする')
        self.auto_save_checkbox.setChecked(self.auto_save)
        self.auto_save_checkbox.stateChanged.connect(self.toggle_auto_save)
        layout.addWidget(self.auto_save_checkbox)
        
        # 終了ボタン
        exit_btn = QPushButton('終了')
        exit_btn.clicked.connect(self.close_application)
        layout.addWidget(exit_btn)
        
        self.setLayout(layout)
        
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        icon_path = resource_path('icon.png')
        self.tray_icon.setIcon(QIcon(icon_path))
        
        # トレイメニューの作成
        tray_menu = QMenu()
        
        # ウィンドウ表示アクション
        show_action = QAction('設定を表示', self)
        show_action.triggered.connect(self.show)
        tray_menu.addAction(show_action)
        
        # スクリーンショット保存アクション
        save_action = QAction('スクリーンショットを保存', self)
        save_action.triggered.connect(self.save_screenshot)
        tray_menu.addAction(save_action)
        
        # 自動保存トグルアクション
        self.auto_save_action = QAction('自動保存: オフ', self)
        self.auto_save_action.triggered.connect(self.toggle_auto_save_from_menu)
        tray_menu.addAction(self.auto_save_action)
        
        tray_menu.addSeparator()
        
        # 終了アクション
        exit_action = QAction('終了', self)
        exit_action.triggered.connect(self.close_application)
        tray_menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()
        
    def load_config(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                self.save_path = config.get('save_path')
                self.auto_save = config.get('auto_save', False)
        else:
            # デフォルトの保存先を設定
            username = os.getenv('USERNAME')
            self.save_path = f'C:\\Users\\{username}\\Pictures\\screenshots'
            self.auto_save = False
            self.save_config()
            
    def save_config(self):
        config = {
            'save_path': self.save_path,
            'auto_save': self.auto_save
        }
        with open(self.config_file, 'w') as f:
            json.dump(config, f)
            
    def change_save_path(self):
        new_path = QFileDialog.getExistingDirectory(self, '保存先を選択', self.save_path)
        if new_path:
            self.save_path = new_path
            self.path_label.setText(f'保存先: {self.save_path}')
            self.save_config()
            
    def reset_path(self):
        username = os.getenv('USERNAME')
        self.save_path = f'C:\\Users\\{username}\\Pictures\\screenshots'
        self.path_label.setText(f'保存先: {self.save_path}')
        self.save_config()
        
    def toggle_auto_save(self, state):
        self.auto_save = bool(state)
        self.save_config()
        self.update_auto_save_status()
        
    def toggle_auto_save_from_menu(self):
        self.auto_save = not self.auto_save
        self.auto_save_checkbox.setChecked(self.auto_save)
        self.save_config()
        self.update_auto_save_status()
        
    def update_auto_save_status(self):
        if self.auto_save:
            self.auto_save_action.setText('自動保存: オン')
            self.auto_save_timer.start(1000)  # 1秒ごとにチェック
        else:
            self.auto_save_action.setText('自動保存: オフ')
            self.auto_save_timer.stop()
            
    def check_clipboard(self):
        try:
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                if data != self.last_clipboard_data:
                    self.last_clipboard_data = data
                    self.save_screenshot()
            win32clipboard.CloseClipboard()
        except:
            pass
            
    def save_screenshot(self):
        try:
            # クリップボードから画像を取得
            win32clipboard.OpenClipboard()
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_DIB):
                data = win32clipboard.GetClipboardData(win32clipboard.CF_DIB)
                win32clipboard.CloseClipboard()
                
                # 画像を保存
                if not os.path.exists(self.save_path):
                    os.makedirs(self.save_path)
                    
                # ファイル名を生成（タイムスタンプ付き）
                from datetime import datetime
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'screenshot_{timestamp}.png'
                filepath = os.path.join(self.save_path, filename)
                
                # 画像を保存
                image = Image.open(io.BytesIO(data))
                image.save(filepath)
                
                self.tray_icon.showMessage('成功', f'スクリーンショットを保存しました: {filename}',
                                         QSystemTrayIcon.Information, 2000)
            else:
                self.tray_icon.showMessage('エラー', 'クリップボードに画像がありません',
                                         QSystemTrayIcon.Warning, 2000)
        except Exception as e:
            self.tray_icon.showMessage('エラー', f'保存に失敗しました: {str(e)}',
                                     QSystemTrayIcon.Critical, 2000)
            
    def closeEvent(self, event):
        # ウィンドウを閉じてもアプリケーションは終了せず、システムトレイに常駐
        event.ignore()
        self.hide()
        
    def close_application(self):
        self.auto_save_timer.stop()
        self.tray_icon.hide()
        QApplication.quit()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ScreenshotApp()
    window.show()
    sys.exit(app.exec_())
