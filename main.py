from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.clock import Clock # UI更新用に追加

import os
import pathlib
import shutil
import threading # 別スレッド実行用に追加
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
        
        # 状態・進捗表示ラベル
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
            
        # ボタンを連打されないように無効化（任意）
        self.select_btn.disabled = True
        self.status_label.text = f"準備中... (0 / {len(selection)})"
        
        # 画面フリーズを防ぐため、重い処理を別スレッドで開始
        threading.Thread(
            target=self.compress_multiple_files_thread, 
            args=(selection,), 
            daemon=True
        ).start()

    # 別スレッドで実行される処理
    def compress_multiple_files_thread(self, file_paths):
        img_count = 0
        video_count = 0
        total_files = len(file_paths)
        
        if platform == "android":
            out_folder = "/sdcard/Download/PapaAlbum_Outputs"
        else:
            out_folder = "./PapaAlbum_Outputs"
            
        try:
            os.makedirs(out_folder, exist_ok=True)
        except Exception as e:
            # メインスレッドのUIを更新
            Clock.schedule_once(lambda dt: self.update_status(f"フォルダ作成エラー: {str(e)}"))
            Clock.schedule_once(lambda dt: self.enable_button())
            return
        
        # 1枚ずつ処理しながら進捗をカウント
        for index, input_path in enumerate(file_paths, start=1):
            # 進行状況を画面にリアルタイム反映 (例: "処理中... (3 / 10)")
            Clock.schedule_once(
                lambda dt, idx=index: self.update_status(f"処理中... ({idx} / {total_files})")
            )
            
            if not input_path or os.path.isdir(input_path):
                continue
                
            ext = pathlib.Path(input_path).suffix.lower()
            filename = os.path.basename(input_path)
            output_path = os.path.join(out_folder, filename)
            
            try:
                timestamp = os.path.getmtime(input_path)
                
                # --- 画像処理 ---
                if ext in [".jpg", ".jpeg", ".png"]:
                    img = Image.open(input_path)
                    img.thumbnail((3000, 3000))
                    
                    if ext in [".jpg", ".jpeg"]:
                        exif_dict = piexif.load(img.info.get("exif", b""))
                        exif_bytes = piexif.dump(exif_dict)
                        img.save(output_path, "jpeg", exif=exif_bytes)
                    else:
                        img.save(output_path)
                        
                    os.utime(output_path, (timestamp, timestamp))
                    img_count += 1
                    
                # --- 動画処理 ---
                elif ext in [".mp4", ".mov", ".m4v"]:
                    shutil.copy2(input_path, output_path)
                    os.utime(output_path, (timestamp, timestamp))
                    video_count += 1
                    
            except Exception as e:
                print(f"Error {input_path}: {e}")
                    
        # すべての処理が完了した時の画面更新
        total = img_count + video_count
        if total > 0:
            result_text = f"完了！ {img_count}枚の画像と{video_count}本の動画を処理しました。\n保存先: {out_folder}"
        else:
            result_text = "ファイルの処理に失敗しました。"
            
        Clock.schedule_once(lambda dt: self.update_status(result_text))
        Clock.schedule_once(lambda dt: self.enable_button())

    # メインスレッドで安全に文字書き換えを行うための関数
    def update_status(self, text):
        self.status_label.text = text

    # メインスレッドで安全にボタンを再有効化するための関数
    def enable_button(self):
        self.select_btn.disabled = False

class PapaAlbumApp(App):
    def build(self):
        return MainLayout()

if __name__ == "__main__":
    PapaAlbumApp().run()
