from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform
from kivy.core.text import LabelBase
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore # 同意フラグ保存用

import os
import pathlib
import shutil
import threading
import webbrowser # ポリシーURL等を開く用
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

# --- カラーパレット定義（パパ・子ども向けの柔らかいアースカラー） ---
COLOR_BG = (0.99, 0.98, 0.96, 1)        # 温かみのあるミルク色 (#FDFBF9)
COLOR_TEXT = (0.29, 0.22, 0.17, 1)      # 優しいダークブラウン (#4A382C)
COLOR_PRIMARY = (0.90, 0.58, 0.39, 1)   # ソフトなテラコッタオレンジ (#E69467)
COLOR_SECONDARY = (0.45, 0.62, 0.51, 1) # 落ち着いたリーフグリーン (#739E82)

class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # 背景色の設定
        with self.canvas.before:
            Color(*COLOR_BG)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        # アプリタイトル表示
        self.title_label = Label(
            text="PapaAlbum - パパの思い出写真圧縮",
            font_size='20sp',
            bold=True,
            color=COLOR_TEXT,
            size_hint_y=0.1,
            font_name=FONT_NAME
        )
        self.add_widget(self.title_label)
        
        # 状態・進捗表示ラベル
        self.status_label = Label(
            text="下のボタンから画像・動画を選択してください", 
            color=COLOR_TEXT,
            size_hint_y=0.2,
            font_name=FONT_NAME,
            halign='center',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.add_widget(self.status_label)
        
        # 実行ボタン（メインアクション）
        self.select_btn = Button(
            text="画像・動画を選択して処理", 
            size_hint_y=0.5,
            font_name=FONT_NAME,
            font_size='18sp',
            bold=True,
            background_color=(0, 0, 0, 0), # 標準スキンを消す
            color=(1, 1, 1, 1)
        )
        with self.select_btn.canvas.before:
            Color(*COLOR_PRIMARY)
            self.btn_rect = Rectangle(size=self.select_btn.size, pos=self.select_btn.pos)
        self.select_btn.bind(size=self._update_btn_rect, pos=self._update_btn_rect)
        self.select_btn.bind(on_press=self.open_file_picker)
        self.add_widget(self.select_btn)
        
        # フッターエリア（ストア必須項目：規約リンク・バージョン）
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.15, spacing=10)
        
        self.policy_btn = Button(
            text="免責事項・プライバシーポリシー",
            font_name=FONT_NAME,
            font_size='11sp',
            color=COLOR_TEXT,
            background_color=(0, 0, 0, 0)
        )
        with self.policy_btn.canvas.before:
            Color(*COLOR_SECONDARY)
            self.policy_rect = Rectangle(size=self.policy_btn.size, pos=self.policy_btn.pos)
        self.policy_btn.bind(size=self._update_policy_rect, pos=self._update_policy_rect)
        self.policy_btn.bind(on_press=self.open_policy_url)
        
        version_label = Label(
            text="ver 1.0.0",
            font_size='12sp',
            color=(0.6, 0.5, 0.4, 1),
            size_hint_x=0.3
        )
        
        footer.add_widget(self.policy_btn)
        footer.add_widget(version_label)
        self.add_widget(footer)

    def _update_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_btn_rect(self, instance, value):
        self.btn_rect.pos = instance.pos
        self.btn_rect.size = instance.size

    def _update_policy_rect(self, instance, value):
        self.policy_rect.pos = instance.pos
        self.policy_rect.size = instance.size

    def open_policy_url(self, instance):
        # Google Playストア公開時に用意するプライバシーポリシーURLをここに記載します
        url = "https://thanks1114.org/papaalbum-policy" 
        webbrowser.open(url)

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
            
        self.select_btn.disabled = True
        self.status_label.text = f"準備中... (0 / {len(selection)})"
        
        threading.Thread(
            target=self.compress_multiple_files_thread, 
            args=(selection,), 
            daemon=True
        ).start()

    def compress_multiple_files_thread(self, file_paths):
        img_count = 0
        video_count = 0
        total_files = len(file_paths)
        
        # 基本となる保存ルートの設定
        if platform == "android":
            try:
                base_dir = storagepath.get_primary_external_storage_dir()
                download_dir = os.path.join(base_dir, "Download")
            except Exception:
                download_dir = App.get_running_app().user_data_dir
        else:
            download_dir = "./"

        for index, input_path in enumerate(file_paths, start=1):
            Clock.schedule_once(
                lambda dt, idx=index: self.update_status(f"パパ頑張り中... ({idx} / {total_files})")
            )
            
            if not input_path or os.path.isdir(input_path):
                continue
                
            # --- 【新仕様】元ファイルのフォルダ名を取得して「_PapaAlbum」を付与 ---
            try:
                input_path_obj = pathlib.Path(input_path)
                parent_folder_name = input_path_obj.parent.name # 例: "Camera" や "Screenshots"
                
                # 元フォルダ名が取得できないか空の場合はデフォルト名にするセーフティ
                if not parent_folder_name:
                    parent_folder_name = "Media"
                    
                # 出力先フォルダの決定（例: Download/Camera_PapaAlbum）
                out_folder = os.path.join(download_dir, f"{parent_folder_name}_PapaAlbum")
                os.makedirs(out_folder, exist_ok=True)
            except Exception as e:
                print(f"Folder creation error for {input_path}: {e}")
                continue
            # -------------------------------------------------------------------
                
            ext = input_path_obj.suffix.lower()
            filename = input_path_obj.name
            output_path = os.path.join(out_folder, filename)
            
            try:
                timestamp = os.path.getmtime(input_path)
                
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
                    
                elif ext in [".mp4", ".mov", ".m4v"]:
                    shutil.copy2(input_path, output_path)
                    os.utime(output_path, (timestamp, timestamp))
                    video_count += 1
                    
            except Exception as e:
                print(f"Error {input_path}: {e}")
                    
        total = img_count + video_count
        if total > 0:
            result_text = f"スッキリ完了！\n画像 {img_count}枚 / 動画 {video_count}本 を整理しました！\n\n保存先:\nAndroid内の「ダウンロード」フォルダ配下"
        else:
            result_text = "ファイルの処理に失敗しました。"
            
        Clock.schedule_once(lambda dt: self.update_status(result_text))
        Clock.schedule_once(lambda dt: self.enable_button())
        
    

    def update_status(self, text):
        self.status_label.text = text

    def enable_button(self):
        self.select_btn.disabled = False

class PapaAlbumApp(App):
    def build(self):
        return MainLayout()

    def on_start(self):
        # 初回起動時の免責事項同意チェック
        self.store = JsonStore('papaalbum_settings.json')
        if not self.store.exists('user_agreement') or not self.store.get('user_agreement')['accepted']:
            self.show_disclaimer_popup()

    def show_disclaimer_popup(self):
        # 免責事項の文言定義
        disclaimer_text = (
            "【重要・免責事項のご確認】\n\n"
            "PapaAlbum（以下、本アプリ）をご利用いただきありがとうございます。\n"
            "ストア公開および有料提供にあたり、以下の免責事項へ同意いただく必要があります。\n\n"
            "1. データの保護について\n"
            "本アプリは画像・動画の圧縮およびコピーを行いますが、万が一の不具合や予期せぬエラーにより、"
            "元データまたは処理後のデータが破損・消失した場合であっても、開発者は一切の責任を負いません。 "
            "重要な思い出のデータは、必ず事前に対象外のクラウドやPC等へバックアップを取った上でご利用ください。\n\n"
            "2. 動作保証について\n"
            "お使いの端末のOSバージョンや空き容量、ハードウェア特性によっては正常に動作しない場合があります。 "
            "本アプリを利用したことによる直接的・間接的な損害（端末の不具合、利益の損失等）について、"
            "開発者は一切の損害賠償責任を負わないものとします。\n\n"
            "3. アップデートと仕様変更について\n"
            "OSのアップデート等に伴い、予告なく仕様変更やサポートの終了を行う場合があります。\n\n"
            "上記内容に同意いただける場合は、下記の「同意して利用を開始」を押してください。"
        )

        # スクロール可能なテキストエリアを作成
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        scroll = ScrollView(size_hint=(1, 0.8))
        
        text_label = Label(
            text=disclaimer_text,
            font_name=FONT_NAME,
            font_size='13sp',
            color=(0.95, 0.95, 0.95, 1),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        text_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
        text_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        scroll.add_widget(text_label)
        content.add_widget(scroll)

        # 同意ボタン
        agree_btn = Button(
            text="同意して利用を開始",
            font_name=FONT_NAME,
            size_hint=(1, 0.2),
            bold=True
        )
        content.add_widget(agree_btn)

        popup = Popup(
            title="ご利用規約・免責事項",
            font_name=FONT_NAME,
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False # 同意するまで閉じられないようにする
        )

        def on_agree(instance):
            # 同意フラグを内部ストレージへ保存
            self.store.put('user_agreement', accepted=True)
            popup.dismiss()

        agree_btn.bind(on_press=on_agree)
        popup.open()

if __name__ == "__main__":
    PapaAlbumApp().run()
