from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.utils import platform

import os
import pathlib
from PIL import Image
# ※事前に pip install piexif して、buildozer.spec の requirements に追加してください
import piexif 

class PapaAlbumButton(Button):
    pass

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        # 状態表示ラベル
        self.status_label = Label(
            text="処理するフォルダ（または画像）を選択してください", 
            size_hint_y=0.1
        )
        self.add_widget(self.status_label)
        
        # ファイル・フォルダセレクター (Androidの初期パスを考慮)
        init_path = "/sdcard" if platform == "android" else os.path.expanduser("~")
        self.file_chooser = FileChooserListView(path=init_path, dirselect=True)
        self.add_widget(self.file_chooser)
        
        # 実行ボタン
        self.run_btn = Button(text="選択したフォルダを圧縮開始", size_hint_y=0.15)
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
        os.makedirs(out_folder, exist_ok=True)
        
        # 簡易的に画像だけを処理する例
        success_count = 0
        for filename in os.listdir(folder_path):
            input_path = os.path.join(folder_path, filename)
            output_path = os.path.join(out_folder, filename)
            
            if not os.path.isfile(input_path):
                continue
                
            ext = pathlib.Path(input_path).suffix.lower()
            if ext in [".jpg", ".jpeg"]:
                try:
                    # タイムスタンプ取得
                    timestamp = os.path.getmtime(input_path)
                    
                    # 画像リサイズ
                    img = Image.open(input_path)
                    img.thumbnail((3000, 3000)) # 長辺を最大3000に維持して縮小
                    
                    # Exifのコピー（piexifを使用）
                    exif_dict = piexif.load(img.info.get("exif", b""))
                    exif_bytes = piexif.dump(exif_dict)
                    
                    # 保存
                    img.save(output_path, "jpeg", exif=exif_bytes)
                    
                    # タイムスタンプの復元
                    os.utime(output_path, (timestamp, timestamp))
                    success_count += 1
                except Exception as e:
                    print(f"Error {filename}: {e}")
                    
        self.status_label.text = f"完了！ {success_count}枚の画像を圧縮しました\n保存先: {out_folder}"

class PapaAlbumApp(App):
    def build(self):
        return MainLayout()
    
    def on_start(self):
        # Android環境の場合、ストレージ読み書き権限をリクエスト
        if platform == "android":
            from android.permissions import request_permissions, Permission
            request_permissions([
                Permission.READ_EXTERNAL_STORAGE, 
                Permission.WRITE_EXTERNAL_STORAGE
            ])

if __name__ == "__main__":
    PapaAlbumApp().run()
