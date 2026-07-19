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
COLOR_BG = (0.99, 0.98, 0.96, 1)       # 温かみのあるミルク色 (#FDFBF9)
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
            size_hint_y=0.1,
            font_name=FONT_NAME,
            halign='center',
            valign='middle'
        )
        self.status_label.bind(size=self.status_label.setter('text_size'))
        self.add_widget(self.status_label)

        # --- 【追加】スクロール可能なログ表示エリア ---
        self.log_scroll = ScrollView(
            size_hint_y=0.3,
            bar_width=10,
            scroll_type=[' Iraqi', 'bars']
        )
        # ログエリアの背景（薄いグレー）
        with self.log_scroll.canvas.before:
            Color(0.93, 0.91, 0.88, 1)
            self.log_bg_rect = Rectangle(size=self.log_scroll.size, pos=self.log_scroll.pos)
        self.log_scroll.bind(size=self._update_log_bg, pos=self._update_log_bg)

        self.log_label = Label(
            text="【アプリログ】\n",
            font_name=FONT_NAME,
            font_size='11sp',
            color=(0.3, 0.3, 0.3, 1),
            size_hint_y=None,
            halign='left',
            valign='top'
        )
        self.log_label.bind(size=lambda instance, value: setattr(instance, 'text_size', (value[0], None)))
        self.log_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        
        self.log_scroll.add_widget(self.log_label)
        self.add_widget(self.log_scroll)
        # --------------------------------------------
        
        # 実行ボタン（メインアクション）
        self.select_btn = Button(
            text="画像・動画を選択して処理", 
            size_hint_y=0.3,
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
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.1, spacing=10)
        
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

    def _update_log_bg(self, instance, value):
        self.log_bg_rect.pos = instance.pos
        self.log_bg_rect.size = instance.size

    # ログを画面上のログエリアに追記する関数
    def write_log(self, text):
        def _append_text(dt):
            self.log_label.text += f"{text}\n"
            # 自動スクロール（常に最下部を表示）
            self.log_scroll.scroll_y = 0
        Clock.schedule_once(_append_text)

    def open_policy_url(self, instance):
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
                self.write_log(f"[ERROR] ピッカー起動失敗: {str(e)}")
        else:
            self.status_label.text = "PC環境では Plyer のファイルピッカーが動作しません"
            self.write_log("[INFO] PC環境のためファイルピッカーをスキップしました")

    def on_file_selected(self, selection):
        if not selection:
            self.status_label.text = "キャンセルされました"
            self.write_log("[INFO] ファイル選択がキャンセルされました")
            return
            
        self.select_btn.disabled = True
        self.status_label.text = f"準備中... (0 / {len(selection)})"
        self.write_log(f"[INFO] {len(selection)}個のファイルが選択されました。処理を開始します...")
        
        threading.Thread(
            target=self.compress_multiple_files_thread, 
            args=(selection,), 
            daemon=True
        )