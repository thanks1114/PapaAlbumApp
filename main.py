from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.core.text import LabelBase

import os
import pathlib
import shutil
from PIL import Image
import piexif 

# --- 日本語フォントの登録 ---
FONT_NAME = "ja_font"
if platform == "android":
    # Androidシステムに内蔵されている日本語フォントのパス
    font_path = "/system/fonts/NotoSansCJK-Regular.ttc"
    if not os.path.exists(font_path):
        font_path = "/system/fonts/DroidSansFallback.ttf"
else:
    # PC環境（Windows/Mac）でテストする場合は、同じフォルダにフォントファイルを置いて指定してください
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
            text="下のボタンから画像・動画を選択してください", 
            size_hint_y=0.3,
            font_name=FONT_NAME
        )
        self.add_widget(self.status_label)
        
        # 実行ボタン
        self.select_btn = Button(
            text="画像・動画を選択して処理", 
            size_hint_y=0.7,
            font_name=FONT_NAME
        )
        self.select_btn.bind(on_press=self.open_file_picker)
        self.add_widget(self.select_btn)

    def open_file_picker(self, instance):
        if platform == "android":
            try:
                from plyer import filechooser
                # 起動失敗を防ぐため、最も汎用的な形式でメディアピッカーを呼び出す
                filechooser.open_file(
                    multiple=True,
                    filters=[("Media", "*/*")], 
                    on_selection=self.on_file_selected
                )
            except Exception as e:
                self.status_label.text = f"ピッカー起動エラー: {str(e)}"
        else:
            self.status_label.text = "PC環境では Plyer のファイルピッカーが動作しません"

    def on_file_selected(self, selection):
        if not selection:
            self.status_label.text = "キャンセルされました"
            return
            
        self.status_label.text = "処理中..."
        self.compress_multiple_files(selection)

    def compress_multiple_files(self, file_paths):
        img_count = 0
        video_count = 0
        
        # Androidでの安全な共通保存先（Downloadフォルダ）
        if platform == "android":
            out_folder = "/sdcard/Download/PapaAlbum_Outputs"
        else:
            out_folder = "./PapaAlbum_Outputs"
            
        try:
            os.makedirs(out_folder, exist_ok=True)
        except Exception as e:
            self.status_label.text = f"フォルダ作成エラー: {str(e)}"
            return
        
        for input_path in file_paths:
            if not input_path or os.path.isdir(input_path):
                continue
                
            ext = pathlib.Path(input_path).suffix.lower()
            filename = os.path.basename(input_path)
            output_path = os.path.join(out_folder, filename)
            
            try:
                # 元ファイルのタイムスタンプを取得
                timestamp = os.path.getmtime(input_path)
                
                # --- 画像処理（JPG/JPEG/PNG） ---
                if ext in [".jpg", ".jpeg", ".png"]:
                    img = Image.open(input_path)
                    img.thumbnail((3000, 3000)) # 長辺を最大3000に維持
                    
                    if ext in [".jpg", ".jpeg"]:
                        # Exif情報を取得してコピー
                        exif_dict = piexif.load(img.info.get("exif", b""))
                        exif_bytes = piexif.dump(exif_dict)
                        img.save(output_path, "jpeg", exif=exif_bytes)
                    else:
                        img.save(output_path)
                        
                    # タイムスタンプ（撮影日等）を維持
                    os.utime(output_path, (timestamp, timestamp))
                    img_count += 1
                    
                # --- 動画処理（MP4/MOV/M4V） ---
                elif ext in [".mp4", ".mov", ".m4v"]:
                    # 動画はコピーし、タイムスタンプのみ維持
                    shutil.copy2(input_path, output_path)
                    os.utime(output_path, (timestamp, timestamp))
                    video_count += 1
                    
            except Exception as e:
                print(f"Error {input_path}: {e}")
                    
        total = img_count + video_count
        if total > 0:
            self.status_label.text = f"完了！ {img_count}枚の画像と{video_count}本の動画を処理しました。\n保存先: {out_folder}"
        else:
            self.status_label.text = "ファイルの処理に失敗しました。対応形式をご確認ください。"

class PapaAlbumApp(App):
    def build(self):
        return MainLayout()

if __name__ == "__main__":
    PapaAlbumApp().run()
