from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.core.text import LabelBase

import os
import pathlib
from PIL import Image
import piexif 

# --- 日本語フォントの登録 ---
FONT_NAME = "ja_font"
if platform == "android":
    font_path = "/system/fonts/NotoSansCJK-Regular.ttc"
    if not os.path.exists(font_path):
        font_path = "/system/fonts/DroidSansFallback.ttf"
else:
    font_path = "NotoSansJP-Regular.ttf"

if os.path.exists(font_path):
    LabelBase.register(name=FONT_NAME, fn_regular=font_path)
else:
    FONT_NAME = None

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        # 状態表示ラベル
        self.status_label = Label(
            text="下のボタンから画像を選択してください", 
            size_hint_y=0.3,
            font_name=FONT_NAME
        )
        self.add_widget(self.status_label)
        
        # 画像選択＆実行ボタン
        self.select_btn = Button(
            text="画像を選択して圧縮（複数可）", 
            size_hint_y=0.7,
            font_name=FONT_NAME
        )
        self.select_btn.bind(on_press=self.open_file_picker)
        self.add_widget(self.select_btn)

    def open_file_picker(self, instance):
        if platform == "android":
            from plyer import filechooser
            # Androidネイティブのギャラリー/ファイル選択画面を呼び出す
            filechooser.open_file(
                multiple=True,
                on_selection=self.on_file_selected
            )
        else:
            # PC環境でのテスト用（ダミー表示またはPC用ダイアログ）
            self.status_label.text = "PC環境では Plyer のファイルピッカーが動作しません"

    def on_file_selected(self, selection):
        # 選択がキャンセルされた場合や空の場合
        if not selection:
            self.status_label.text = "キャンセルされました"
            return
            
        self.status_label.text = "処理中..."
        self.compress_multiple_files(selection)

    def compress_multiple_files(self, file_paths):
        success_count = 0
        
        for input_path in file_paths:
            # Androidのピッカーから渡される特殊なパスのチェック
            if not input_path or os.path.isdir(input_path):
                continue
                
            ext = pathlib.Path(input_path).suffix.lower()
            # ピッカーによっては拡張子が取得できない場合があるため、画像として処理を試行
            try:
                parent_dir = os.path.dirname(input_path)
                filename = os.path.basename(input_path)
                
                # Android 10以降の共有ストレージ書き込み制限を考慮し、
                # アプリのプライベートキャッシュ領域または特定のパブリックディレクトリに保存
                if platform == "android":
                    # Androidの場合は、安全に書き込める「Download」フォルダなどを指定
                    out_folder = "/sdcard/Download/PapaAlbum_Outputs"
                else:
                    out_folder = parent_dir + "_PapaAlbum"
                    
                os.makedirs(out_folder, exist_ok=True)
                output_path = os.path.join(out_folder, filename)
                
                # タイムスタンプ取得
                timestamp = os.path.getmtime(input_path)
                
                # 画像リサイズ
                img = Image.open(input_path)
                img.thumbnail((3000, 3000))
                
                # Exifのコピー
                exif_dict = piexif.load(img.info.get("exif", b""))
                exif_bytes = piexif.dump(exif_dict)
                
                # 保存
                img.save(output_path, "jpeg", exif=exif_bytes)
                os.utime(output_path, (timestamp, timestamp))
                success_count += 1
            except Exception as e:
                print(f"Error {input_path}: {e}")
                    
        if success_count > 0:
            self.status_label.text = f"完了！ {success_count}枚の画像を圧縮しました。\n保存先: /sdcard/Download/PapaAlbum_Outputs"
        else:
            self.status_label.text = "画像の処理に失敗しました。権限やファイル形式を確認してください。"

class PapaAlbumApp(App):
    def build(self):
        return MainLayout()

if __name__ == "__main__":
    PapaAlbumApp().run()
