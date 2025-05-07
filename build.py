import PyInstaller.__main__
import os

# アイコンファイルの存在確認
if not os.path.exists('icon.png'):
    print('エラー: icon.pngが見つかりません。')
    exit(1)

PyInstaller.__main__.run([
    'main.py',
    '--name=ScreenshotSaver',
    '--onefile',
    '--windowed',
    '--icon=icon.png',
    '--add-data=icon.png;.',
    '--clean',
    '--noconfirm'
]) 