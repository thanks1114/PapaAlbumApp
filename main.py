import os
import pathlib
import shutil
import threading
import time
import webbrowser
from datetime import datetime
from PIL import Image, ImageOps

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
from kivy.core.window import Window

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
    Androidの content:// URI から安全にファイルをコピーし、
    (一時パス, ファイル名, 元の親フォルダ名) を返す関数
    """
    if not uri_str.startswith("content://"):
        parent_name = pathlib.Path(uri_str).parent.name
        filename = pathlib.Path(uri_str).name
        return uri_str, filename, parent_name

    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            Uri = autoclass('android.net.Uri')
            
            uri = Uri.parse(uri_str)
            resolver = context.getContentResolver()
            
            filename = "temp_media_file"
            parent_folder_name = "Media"
            
            # MIMEタイプ取得（拡張子補完用）
            mime_type = resolver.getType(uri)
            
            # メタデータからファイル名と元フォルダ名を取得
            try:
                MediaStore = autoclass('android.provider.MediaStore')
                projection = [MediaStore.MediaColumns.DATA, MediaStore.MediaColumns.DISPLAY_NAME]
                cursor = resolver.query(uri, projection, None, None, None)
                
                if cursor is not None and cursor.moveToFirst():
                    name_index = cursor.getColumnIndex(MediaStore.MediaColumns.DISPLAY_NAME)
                    if name_index != -1:
                        fetched_name = cursor.getString(name_index)
                        if fetched_name:
                            filename = fetched_name
                    
                    data_index = cursor.getColumnIndex(MediaStore.MediaColumns.DATA)
                    if data_index != -1:
                        real_path = cursor.getString(data_index)
                        if real_path:
                            parent_folder_name = pathlib.Path(real_path).parent.name
                            
                    cursor.close()
            except Exception as e:
                print(f"Failed to query MediaStore metadata: {e}")

            # 拡張子がない場合の補完処理
            if not pathlib.Path(filename).suffix and mime_type:
                if "jpeg" in mime_type or "jpg" in mime_type:
                    filename += ".jpg"
                elif "png" in mime_type:
                    filename += ".png"
                elif "webp" in mime_type:
                    filename += ".webp"
                elif "mp4" in mime_type:
                    filename += ".mp4"
                elif "quicktime" in mime_type or "mov" in mime_type:
                    filename += ".mov"

            # キャッシュディレクトリへ一時コピー
            temp_path = os.path.join(cache_dir, filename)
            
            input_stream = resolver.openInputStream(uri)
            if input_stream is None:
                raise IOError("openInputStream returned None")

            FileOutputStream = autoclass('java.io.FileOutputStream')
            output_stream = FileOutputStream(temp_path)
            
            buffer = bytearray(1024 * 1024)
            while True:
                bytes_read = input_stream.read(buffer)
                if bytes_read <= 0:
                    break
                output_stream.write(buffer, 0, bytes_read)
                
            input_stream.close()
            output_stream.close()
            
            return temp_path, filename, parent_folder_name
        except Exception as e:
            print(f"Failed to copy content URI: {e}")
            return None, None, "Media"
            
    return uri_str, pathlib.Path(uri_str).name, "Media"


def get_exif_mtime(img, fallback_mtime):
    """画像からExif撮影日時を取得しタイムスタンプ(epoch sec)で返す。取得不可ならfallback_mtimeを返す"""
    try:
        exif = img.getexif()
        # 36867 = DateTimeOriginal, 306 = DateTime
        date_str = exif.get(36867) or exif.get(306)
        if date_str:
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            return dt.timestamp()
    except Exception:
        pass
    return fallback_mtime


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        # ウインドウリサイズ時の描画安定化
        Window.bind(on_resize=lambda *args: Window.canvas.ask_update())
        
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
                from jnius import autoclass
                from android.activity import bind, unbind
                
                try:
                    unbind(on_activity_result=self.on_activity_result)
                except Exception:
                    pass
                
                PythonActivity = autoclass('org.kivy.android.PythonActivity')
                Intent = autoclass('android.content.Intent')
                String = autoclass('java.lang.String')
                
                intent = Intent(Intent.ACTION_GET_CONTENT)
                intent.setType("*/*")
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, True)
                intent.addCategory(Intent.CATEGORY_OPENABLE)
                
                bind(on_activity_result=self.on_activity_result)
                
                chooser_intent = Intent.createChooser(intent, String("メディアを選択"))
                PythonActivity.mActivity.startActivityForResult(chooser_intent, 1001)
                
                self.write_log("[INFO] Native Intent ピッカーを起動しました")
            except Exception as e:
                self.status_label.text = f"ピッカー起動エラー: {str(e)}"
                self.write_log(f"[ERROR] ピッカー起動失敗: {str(e)}")
        else:
            self.write_log("[INFO] Android端末上でのみ動作します")

    def on_activity_result(self, request_code, result_code, intent):
        if request_code == 1001:
            try:
                from android.activity import unbind
                unbind(on_activity_result=self.on_activity_result)
            except Exception:
                pass
            
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
                    threading.Thread(
                        target=self.process_selected_files_thread,
                        args=(selected_uris,),
                        daemon=True
                    ).start()
                else:
                    self.status_label.text = "ファイルが選択されませんでした"
                    self.write_log("[INFO] ファイルが選択されませんでした")
            else:
                self.status_label.text = "キャンセルされました"
                self.write_log("[INFO] ファイル選択がキャンセルされました")

    def process_selected_files_thread(self, file_paths):
        """ファイル選択後の処理（圧縮・保存）"""
        Clock.schedule_once(lambda dt: self._prepare_processing_ui(len(file_paths)))
        
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
                
            working_path, original_filename, parent_folder_name = get_real_path_or_copy(raw_input_path, cache_dir)
            
            if not working_path or working_path.startswith("content://"):
                self.write_log(f"[ERROR] ファイルの取得・コピーに失敗しました: {raw_input_path}")
                continue

            try:
                if not parent_folder_name or parent_folder_name in ["/", "\\", "."]:
                    parent_folder_name = "Media"

                out_folder_name = f"{parent_folder_name}_PapaAlbum"
                target_out_dir = os.path.join(base_download_dir, out_folder_name)
                os.makedirs(target_out_dir, exist_ok=True)

                filename = original_filename if original_filename else pathlib.Path(working_path).name
                ext = pathlib.Path(filename).suffix.lower()
                
                output_path = os.path.join(target_out_dir, filename)
                
                try:
                    fallback_mtime = os.path.getmtime(working_path)
                except Exception:
                    fallback_mtime = time.time()
                
                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    self.write_log(f"[PROCESSING] 画像圧縮中: {filename}")
                    
                    with Image.open(working_path) as img:
                        target_mtime = get_exif_mtime(img, fallback_mtime)
                        img = ImageOps.exif_transpose(img)
                        img.thumbnail((3000, 3000))
                        
                        if ext in [".jpg", ".jpeg"]:
                            img.save(output_path, "JPEG", quality=85, optimize=True)
                        else:
                            img.save(output_path, optimize=True)
                    
                    try:
                        os.utime(output_path, (target_mtime, target_mtime))
                    except Exception as e:
                        self.write_log(f"[WARNING] 日付の設定に失敗しました: {e}")
                        
                    img_count += 1
                    self.write_log(f"[SUCCESS] 保存完了: {output_path}")
                    
                elif ext in [".mp4", ".mov", ".m4v"]:
                    self.write_log(f"[PROCESSING] 動画コピー中: {filename}")
                    shutil.copy2(working_path, output_path)
                    video_count += 1
                    self.write_log(f"[SUCCESS] コピー完了: {output_path}")
                else:
                    self.write_log(f"[SKIP] 未対応のファイル形式です: {filename} (拡張子: {ext})")
                    
            except Exception as e:
                self.write_log(f"[ERROR] 処理失敗 {filename}: {e}")
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
            result_text = "ファイルの処理に失敗しました。\nログを確認してください。"
            
        Clock.schedule_once(lambda dt: self.update_status(result_text))
        Clock.schedule_once(lambda dt: self.enable_button())

    def _prepare_processing_ui(self, count):
        self.select_btn.disabled = True
        self.status_label.text = f"準備中... (0 / {count})"
        self.write_log(f"[INFO] {count}個のファイルが選択されました。処理を開始します...")

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
                    Permission.READ_MEDIA_IMAGES,
                    Permission.READ_MEDIA_VIDEO,
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