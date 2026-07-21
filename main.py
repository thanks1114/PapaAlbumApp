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
from kivy.storage.jsonstore import JsonStore
from kivy.core.clipboard import Clipboard

import os
import pathlib
import shutil
import threading
import webbrowser
from PIL import Image, ImageOps

# --- 日本語フォントの登録 ---
FONT_NAME = "ja_font"
if platform == "android":
    font_path = "/system/fonts/NotoSansCJK-Regular.ttc"
    if not os.path.exists(font_path):
        font_path = "/system/fonts/DroidSansFallback.ttf"
else:
    font_path = "NotoSansJP-Regular.ttf"

try:
    if os.path.exists(font_path):
        LabelBase.register(name=FONT_NAME, fn_regular=font_path)
    else:
        FONT_NAME = None
except Exception as e:
    print(f"Font registration failed: {e}")
    FONT_NAME = None

# --- カラーパレット定義 ---
COLOR_BG = (0.99, 0.98, 0.96, 1)
COLOR_TEXT = (0.29, 0.22, 0.17, 1)
COLOR_PRIMARY = (0.90, 0.58, 0.39, 1)
COLOR_SECONDARY = (0.45, 0.62, 0.51, 1)


def get_real_path_or_copy(uri_str, cache_dir):
    """
    Androidの content:// URI から安全にファイルを一時ディレクトリへコピーしてパスを返す関数
    """
    if not uri_str.startswith("content://"):
        return uri_str, None

    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            Uri = autoclass('android.net.Uri')
            
            uri = Uri.parse(uri_str)
            resolver = context.getContentResolver()
            
            filename = "temp_media_file"
            try:
                OpenableColumns = autoclass('android.provider.OpenableColumns')
                cursor = resolver.query(uri, None, None, None, None)
                if cursor is not None and cursor.moveToFirst():
                    name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if name_index != -1:
                        filename = cursor.getString(name_index)
                    cursor.close()
            except Exception:
                pass

            temp_path = os.path.join(cache_dir, filename)
            
            input_stream = resolver.openInputStream(uri)
            FileOutputStream = autoclass('java.io.FileOutputStream')
            output_stream = FileOutputStream(temp_path)
            
            buffer = bytearray(1024 * 64)
            while True:
                bytes_read = input_stream.read(buffer)
                if bytes_read <= 0:
                    break
                output_stream.write(buffer, 0, bytes_read)
                
            input_stream.close()
            output_stream.close()
            return temp_path, filename
        except Exception as e:
            print(f"Failed to copy content URI: {e}")
            return uri_str, None
    return uri_str, None


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        with self.canvas.before:
            Color(*COLOR_BG)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        self.title_label = Label(
            text="PapaAlbum - パパの思い出写真圧縮",
            font_size='20sp',
            bold=True,
            color=COLOR_TEXT,
            size_hint_y=0.1,
            font_name=FONT_NAME
        )
        self.add_widget(self.title_label)
        
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
        
        self.select_btn = Button(
            text="画像・動画を選択して処理", 
            size_hint_y=0.25,
            font_name=FONT_NAME,
            font_size='18sp',
            bold=True,
            background_color=(0, 0, 0, 0),
            color=(1, 1, 1, 1)
        )
        with self.select_btn.canvas.before:
            Color(*COLOR_PRIMARY)
            self.btn_rect = Rectangle(size=self.select_btn.size, pos=self.select_btn.pos)
        self.select_btn.bind(size=self._update_btn_rect, pos=self._update_btn_rect)
        self.select_btn.bind(on_press=self.open_file_picker)
        self.add_widget(self.select_btn)

        self.log_scroll = ScrollView(
            size_hint_y=0.3,
            bar_width=10,
            scroll_type=['bars']
        )
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

        self.copy_log_btn = Button(
            text="ログをクリップボードにコピー",
            font_name=FONT_NAME,
            font_size='12sp',
            size_hint_y=0.08,
            background_color=(0.5, 0.5, 0.5, 1),
            color=(1, 1, 1, 1)
        )
        self.copy_log_btn.bind(on_press=self.copy_log_to_clipboard)
        self.add_widget(self.copy_log_btn)
        
        footer = BoxLayout(orientation='horizontal', size_hint_y=0.08, spacing=10)
        
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

    def write_log(self, text):
        def _append_text(dt):
            self.log_label.text += f"{text}\n"
            self.log_scroll.scroll_y = 0
        Clock.schedule_once(_append_text)

    def copy_log_to_clipboard(self, instance):
        try:
            Clipboard.copy(self.log_label.text)
            old_status = self.status_label.text
            self.status_label.text = "ログをコピーしました！"
            Clock.schedule_once(lambda dt: setattr(self.status_label, 'text', old_status), 2)
            self.write_log("[INFO] ログがクリップボードにコピーされました")
        except Exception as e:
            self.write_log(f"[ERROR] ログのコピーに失敗しました: {e}")

    def open_policy_url(self, instance):
        url = "https://thanks1114.org/papaalbum-policy" 
        webbrowser.open(url)

    def open_file_picker(self, instance):
        if platform == "android":
            try:
                from jnius import autoclass, activity
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("*/*")
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                
                activity.bind(on_activity_result=self.on_activity_result)
                PythonActivity.mActivity.startActivityForResult(
                    Intent.createChooser(intent, "メディアを選択"), 1001
                )
                self.write_log("[INFO] Native Intent ピッカーを起動しました")
            except Exception as e:
                self.status_label.text = f"ピッカー起動エラー: {str(e)}"
                self.write_log(f"[ERROR] ピッカー起動失敗: {str(e)}")
        else:
            self.write_log("[INFO] Android端末上でのみ動作します")

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1001:
            from jnius import autoclass, activity
            activity.unbind(on_activity_result=self.on_activity_result)
            
            # RESULT_OK (-1) チェック
            if result_code == -1 and intent is not None:
                selected_uris = []
                
                clip_data = intent.getClipData()
                if clip_data is not None:
                    count = clip_data.getItemCount()
                    for i in range(count):
                        item = clip_data.getItemAt(i)
                        selected_uris.append(item.getUri().toString())
                else:
                    data_uri = intent.getData()
                    if data_uri is not None:
                        selected_uris.append(data_uri.toString())
                
                if selected_uris:
                    self.on_file_selected(selected_uris)
                else:
                    self.status_label.text = "ファイルが選択されませんでした"
                    self.write_log("[INFO] ファイルが選択されませんでした")
            else:
                self.status_label.text = "キャンセルされました"
                self.write_log("[INFO] ファイル選択がキャンセルされました")

    def on_file_selected(self, selection):
        if not selection:
            self.status_label.text = "キャンセルされました"
            self.write_log("[INFO] ファイル選択がキャンセルされました")
            return
            
        self.select_btn.disabled = True
        self.status_label.text = f"準備中... (0 / {len(selection)})"
        self.write_log(f"[INFO] {len(selection)}個のファイルが選択されました。処理を開始します...")
        
        Clock.schedule_once(lambda dt: threading.Thread(
            target=self.compress_multiple_files_thread, 
            args=(selection,), 
            daemon=True
        ).start(), 0.2)

    def compress_multiple_files_thread(self, file_paths):
        img_count = 0
        video_count = 0
        total_files = len(file_paths)
        
        base_download_dir = "/storage/emulated/0/Download"
        cache_dir = App.get_running_app().user_data_dir

        for index, raw_input_path in enumerate(file_paths, start=1):
            Clock.schedule_once(
                lambda dt, idx=index: self.update_status(f"パパ頑張り中... ({idx} / {total_files})")
            )
            
            if not raw_input_path:
                continue
                
            working_path, original_filename = get_real_path_or_copy(raw_input_path, cache_dir)
            
            try:
                if raw_input_path.startswith("content://"):
                    parent_folder_name = "Media"
                else:
                    parent_folder_name = pathlib.Path(raw_input_path).parent.name
                
                if not parent_folder_name or parent_folder_name in ["/", "\\", "."]:
                    parent_folder_name = "Media"

                out_folder_name = f"{parent_folder_name}_PapaAlbum"
                target_out_dir = os.path.join(base_download_dir, out_folder_name)
                os.makedirs(target_out_dir, exist_ok=True)

                input_path_obj = pathlib.Path(working_path)
                filename = original_filename if original_filename else input_path_obj.name
                ext = pathlib.Path(filename).suffix.lower()
                
                output_path = os.path.join(target_out_dir, filename)
                
                if ext in [".jpg", ".jpeg", ".png"]:
                    self.write_log(f"[PROCESSING] 画像圧縮中: {filename}")
                    
                    with Image.open(working_path) as img:
                        # GPS（位置情報）を含む全EXIFを取得
                        exif_data = img.getexif()
                        
                        # 向き補正
                        img = ImageOps.exif_transpose(img)
                        img.thumbnail((3000, 3000))
                        
                        save_kwargs = {}
                        if exif_data:
                            save_kwargs["exif"] = exif_data
                            
                        if ext in [".jpg", ".jpeg"]:
                            img.save(output_path, "JPEG", quality=85, **save_kwargs)
                        else:
                            img.save(output_path, **save_kwargs)
                        
                    img_count += 1
                    self.write_log(f"[SUCCESS] 保存完了: {output_path}")
                    
                elif ext in [".mp4", ".mov", ".m4v"]:
                    self.write_log(f"[PROCESSING] 動画コピー中: {filename}")
                    shutil.copy2(working_path, output_path)
                    video_count += 1
                    self.write_log(f"[SUCCESS] コピー完了: {output_path}")
                    
            except Exception as e:
                self.write_log(f"[ERROR] 処理失敗 {raw_input_path}: {e}")
            finally:
                if raw_input_path.startswith("content://") and os.path.exists(working_path):
                    try:
                        os.remove(working_path)
                    except Exception:
                        pass
                    
        total = img_count + video_count
        if total > 0:
            result_text = f"スッキリ完了！\n画像 {img_count}枚 / 動画 {video_count}本 を整理しました！\nダウンロードフォルダに保存しました。"
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
        self.store = JsonStore('papaalbum_settings.json')
        if not self.store.exists('user_agreement') or not self.store.get('user_agreement')['accepted']:
            self.show_disclaimer_popup()
            
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.ACCESS_MEDIA_LOCATION
                ])
            except Exception as e:
                print(f"Failed to request permissions: {e}")

    def show_disclaimer_popup(self):
        disclaimer_text = (
            "【重要・免責事項のご確認】\n\n"
            "PapaAlbum（以下、本アプリ）をご利用いただきありがとうございます。\n"
            "ストア公開および有料提供にあたり、以下の免責事項へ同意いただく必要があります。\n\n"
            "1. データの保護について\n"
            "本アプリは画像・動画の圧縮およびコピーを行いますが、万が一の不具合や予期せぬエラーにより、"
            "元データまたは処理後のデータが破損・消失した場合であっても、開発者は一切の責任を負いません。 "
            "重要な思い出のデータは、必ず事前に対象外のクラウドやPC等へバックアップを取った上でご利用ください。\n\n"
            "2. 動作保証について\n"
            "お使いの端末のOSバージョンや空き容量、ハードウェア特性によっては正常に動作しない場合があります。\n\n"
            "上記内容に同意いただける場合は、下記の「同意して利用を開始」を押してください。"
        )

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

        agree_btn = Button(
            text="同意して利用を開始",
            font_name=FONT_NAME,
            size_hint=(1, 0.2),
            bold=True
        )
        content.add_widget(agree_btn)

        popup = Popup(
            title="ご利用規約・免責事項",
            title_font=FONT_NAME,
            content=content,
            size_hint=(0.9, 0.9),
            auto_dismiss=False
        )

        def on_agree(instance):
            self.store.put('user_agreement', accepted=True)
            popup.dismiss()

        agree_btn.bind(on_press=on_agree)
        popup.open()


if __name__ == "__main__":
    PapaAlbumApp().run()