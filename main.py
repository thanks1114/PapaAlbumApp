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
# 独自のフォントファイル（.ttf）を用意してアプリと同フォルダに置くか、
# Androidのシステムフォントのパスを指定します。
FONT_NAME = "ja_font"
if platform == "android":
    # Androidに標準搭載されている日本語対応フォントの例
    font_path = "/system/fonts/NotoSansCJK-Regular.ttc"
    if not os.path.exists(font_path):
        font_path = "/system/fonts/DroidSansFallback.ttf"
else:
    # PC環境（Windows/Mac）でテストする場合は、同じフォルダにフォントファイルを置いて指定してください
    font_path = "NotoSansJP-Regular.ttf" # ←各自用意したフォント名に変更してください

# フォントが存在する場合のみ登録（なければデフォルト）
if os.path.exists(font_path):
    LabelBase.register(name=FONT_NAME, fn_regular=font_path)
else:
    FONT_NAME = None # フォントがない場合はデフォルト（英語のみ）

class PapaAlbumButton(Button):
    pass

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        # 状態表示ラベル（font_name を指定）
        self.status_label = Label(
            text="処理するフォルダを選択してください", 
            size_hint_y=0.1,
            font_name=FONT_NAME
        )
        self.add_widget(self.status_label)
        
        # ファイル・フォルダセレクター
        init_path = "/sdcard" if platform == "android" else os.path.expanduser("~")
        # dirselect=True により「フォルダの選択」を有効にしています
        self.file_chooser = FileChooserListView(path=init_path, dirselect=True)
        self.add_widget(self.file_chooser)
        
        # 実行ボタン（font_name を指定）
        self.run_btn = Button(
            text="選択したフォルダを圧縮開始", 
            size_hint_y=0.15,
            font_name=FONT_NAME
        )
        self.run_btn.bind(on_press=self.start_processing)
        self.add_widget(self.run_btn)

    def start_processing(self, instance):
        selected = self.file_chooser.selection
        if not selected:
            self.status_label.text = "エラー: フォルダが選択されていません"
            return
            
        target_path = selected[0]
        if os.path.isdir(target_path):
            self.status_label.text = "処理中..."
            self.compress_folder_android(target_path)
        else:
            self.status_label.text = "フォルダを選択してください"

    def compress_folder_android(self, folder_path):
        out_folder = folder_path + "_PapaAlbum"
        try:
            os.makedirs(out_folder, exist_ok=True)
        except Exception as e:
            self.status_label.text = f"フォルダ作成エラー: {e}"
            return
        
        success_count = 0
        for filename in os.listdir(folder_path):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(out_folder, filename)
            
            if not os.path.isfile(input_path):
                continue
                
            ext = pathlib.Path(input_path).suffix.lower()
            if ext in [".jpg", ".jpeg"]:
                try:
                    timestamp = os.path.getmtime(input_path)
                    
                    img = Image.open(input_path)
                    img.thumbnail((3000, 3000))
                    
                    exif_dict = piexif.load(img.info.get("exif", b""))
                    exif_bytes = piexif.dump(exif_dict)
                    
                    img.save(output_path, "jpeg", exif=exif_bytes)
                    os.utime(output_path, (timestamp, timestamp))
                    success_count += 1
                except Exception as e:
                    print(f"Error {filename}: {e}")
                    
        self.status_label.text = f"完了！ {success_count}枚の画像を圧縮しました\n保存先: {out_folder}"

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
