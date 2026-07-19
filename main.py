from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
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
    font_path = "NotoSansJP-Regular.ttf" # ←PCテスト時はお手持ちのフォント名に合わせてください

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
            text="処理する画像ファイルを複数選択してください", 
            size_hint_y=0.1,
            font_name=FONT_NAME
        )
        self.add_widget(self.status_label)
        
        # ファイルセレクター (複数ファイル選択対応)
        init_path = "/sdcard" if platform == "android" else os.path.expanduser("~")
        self.file_chooser = FileChooserListView(
            path=init_path, 
            multiselect=True,
            dirselect=False
        )
        self.add_widget(self.file_chooser)
        
        # 実行ボタン
        self.run_btn = Button(
            text="選択したファイルを一括圧縮開始", 
            size_hint_y=0.15,
            font_name=FONT_NAME
        )
        self.run_btn.bind(on_press=self.start_processing)
        self.add_widget(self.run_btn)

    def start_processing(self, instance):
        selected_files = self.file_chooser.selection
        if not selected_files:
            self.status_label.text = "エラー: ファイルが選択されていません"
            return
            
        self.status_label.text = "処理中..."
        self.compress_multiple_files(selected_files)

    def compress_multiple_files(self, file_paths):
        success_count = 0
        processed_folders = set() # 作成したフォルダを記録するセット
        
        for input_path in file_paths:
            if os.path.isdir(input_path):
                continue
                
            ext = pathlib.Path(input_path).suffix.lower()
            if ext in [".jpg", ".jpeg"]:
                try:
                    # 元ファイルがあるフォルダのパスとファイル名を取得
                    parent_dir = os.path.dirname(input_path)
                    filename = os.path.basename(input_path)
                    
                    # 元フォルダ名に「_PapaAlbum」を付与した新しいフォルダパスを作成
                    out_folder = parent_dir + "_PapaAlbum"
                    
                    # まだ作成していないフォルダなら新規作成
                    if out_folder not in processed_folders:
                        os.makedirs(out_folder, exist_ok=True)
                        processed_folders.add(out_folder)
                    
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
            self.status_label.text = f"完了！ {success_count}枚の画像を圧縮しました。\nそれぞれの元フォルダ名_PapaAlbumに格納しました。"
        else:
            self.status_label.text = "対応する画像ファイル（JPG/JPEG）が処理されませんでした"

class PapaAlbumApp(App):
    def build(self):
        return MainLayout()
    
    def on_start(self):
        if platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, 
                Permission.WRITE_EXTERNAL_STORAGE
            ])

if __name__ == "__main__":
    PapaAlbumApp().run()
