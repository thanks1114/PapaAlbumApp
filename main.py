import os
import pathlib
import shutil
import threading
import time
import subprocess
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

import piexif

# --- グローバル変数 ---
FFMPEG_PATH = None

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


def init_ffmpeg_path():
    """
    メインスレッド(JNI有効時)でネイティブFFmpegバイナリのパスを取得しキャッシュする
    """
    global FFMPEG_PATH
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = PythonActivity.mActivity
            
            lib_dir = activity.getApplicationInfo().nativeLibraryDir
            ffmpeg_so = os.path.join(lib_dir, "libffmpeg.so")
            
            if os.path.exists(ffmpeg_so):
                try:
                    os.chmod(ffmpeg_so, 0o755)
                except Exception:
                    pass
                FFMPEG_PATH = ffmpeg_so
                print(f"[INFO] Native FFmpeg resolved: {FFMPEG_PATH}")
            else:
                print(f"[WARNING] libffmpeg.so not found in {lib_dir}")
        except Exception as e:
            print(f"[ERROR] Failed to initialize FFmpeg path: {e}")
    else:
        FFMPEG_PATH = "ffmpeg"


def load_native_libraries():
    """Androidの動的リンカーに合わせて、依存関係順に.soを事前ロードする"""
    if platform == "android":
        try:
            from jnius import autoclass
            System = autoclass('java.lang.System')
            
            System.loadLibrary("SvtAv1Enc")
            System.loadLibrary("avutil")
            System.loadLibrary("swresample")
            System.loadLibrary("avcodec")
            System.loadLibrary("swscale")
            System.loadLibrary("avformat")
            System.loadLibrary("avfilter")
            print("[INFO] 全ネイティブライブラリ(.so)のロードに成功しました")
        except Exception as e:
            print(f"[ERROR] ネイティブライブラリのロードに失敗しました: {e}")


def get_unique_target_path(target_dir, filename):
    """
    同名ファイルが存在する場合に連番(例: photo_1.jpg)を付与して上書きを阻止する
    """
    base_name, ext = os.path.splitext(filename)
    counter = 1
    target_path = os.path.join(target_dir, filename)
    
    while os.path.exists(target_path):
        target_path = os.path.join(target_dir, f"{base_name}_{counter}{ext}")
        counter += 1
        
    return target_path


def get_real_path_or_copy(uri_str, cache_dir):
    """
    Androidの content:// URI から元ファイル名を取得し安全に処理用キャッシュへコピーする
    """
    if not uri_str.startswith("content://"):
        path_obj = pathlib.Path(uri_str)
        return uri_str, path_obj.name, str(path_obj.parent)

    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            context = PythonActivity.mActivity
            Uri = autoclass('android.net.Uri')
            
            uri = Uri.parse(uri_str)
            
            # GPS 位置情報マスキング解除
            try:
                MediaStore = autoclass('android.provider.MediaStore')
                uri = MediaStore.setRequireOriginal(uri)
            except Exception as gps_err:
                print(f"setRequireOriginal not applied: {gps_err}")

            resolver = context.getContentResolver()
            filename = None
            original_parent_dir = None
            
            # OpenableColumns から元ファイル名を取得
            try:
                OpenableColumns = autoclass('android.provider.OpenableColumns')
                cursor = resolver.query(uri, None, None, None, None)
                if cursor is not None and cursor.moveToFirst():
                    name_index = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME)
                    if name_index != -1:
                        filename = cursor.getString(name_index)
                    cursor.close()
            except Exception as e:
                print(f"Failed to query OpenableColumns: {e}")

            # DATA カラムからパス取得（取得可能な場合）
            try:
                MediaStore = autoclass('android.provider.MediaStore')
                projection = [MediaStore.MediaColumns.DATA]
                cursor = resolver.query(uri, projection, None, None, None)
                if cursor is not None and cursor.moveToFirst():
                    data_index = cursor.getColumnIndex(MediaStore.MediaColumns.DATA)
                    if data_index != -1:
                        real_path = cursor.getString(data_index)
                        if real_path and real_path.startswith("/"):
                            original_parent_dir = str(pathlib.Path(real_path).parent)
                            if not filename:
                                filename = pathlib.Path(real_path).name
                    cursor.close()
            except Exception as e:
                print(f"Failed to query MediaStore DATA: {e}")

            # 取得できない場合のファイル名生成
            if not filename or filename == "temp_media_file":
                timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]
                filename = f"Media_{timestamp_str}"

            # 拡張子の補正
            mime_type = resolver.getType(uri)
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

            temp_path = get_unique_target_path(cache_dir, filename)
            
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
            
            return temp_path, pathlib.Path(temp_path).name, original_parent_dir
        except Exception as e:
            print(f"Failed to copy content URI: {e}")
            return None, None, None
            
    path_obj = pathlib.Path(uri_str)
    return uri_str, path_obj.name, str(path_obj.parent)


def get_exif_mtime(img, fallback_mtime):
    """画像からExif撮影日時を取得しタイムスタンプ(epoch sec)で返す"""
    try:
        exif = img.getexif()
        date_str = exif.get(36867) or exif.get(306)
        if date_str:
            dt = datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            return dt.timestamp()
    except Exception:
        pass
    return fallback_mtime


def compress_video_av1(input_path, output_path):
    """FFmpegバイナリを用いたAV1(libsvtav1)動画エンコード処理"""
    global FFMPEG_PATH
    if not FFMPEG_PATH:
        raise FileNotFoundError("FFmpeg バイナリパスが初期化されていません")
    
    cmd = [
        FFMPEG_PATH, "-y",
        "-i", input_path,
        "-vcodec", "libsvtav1",
        "-crf", "32",
        "-preset", "8",
        "-acodec", "aac",
        "-b:a", "128k",
        "-map_metadata", "0",
        "-movflags", "+faststart",
        output_path
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    if process.returncode != 0:
        raise RuntimeError(f"FFmpeg Error: {stderr.decode('utf-8', errors='ignore')}")


class MainLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15
        
        Window.bind(on_resize=lambda *args: Window.canvas.ask_update())
        
        with self.canvas.before:
            Color(*COLOR_BG)
            self.bg_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        self.title_label = Label(
            text="PapaAlbum - パパの思い出写真・動画整理",
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
            text="ver 1.1.0",
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
        """ファイル選択後の処理（画像圧縮・Exif位置情報継承・回転補正・連番生成・動画処理）"""
        Clock.schedule_once(lambda dt: self._prepare_processing_ui(len(file_paths)))
        
        img_count = 0
        video_count = 0
        total_files = len(file_paths)
        
        dcim_dir = "/storage/emulated/0/DCIM"
        pictures_dir = "/storage/emulated/0/Pictures"
        download_dir = "/storage/emulated/0/Download"
        
        cache_dir = App.get_running_app().user_data_dir

        for index, raw_input_path in enumerate(file_paths, start=1):
            Clock.schedule_once(
                lambda dt, idx=index: self.update_status(f"パパ頑張り中... ({idx} / {total_files})")
            )
            
            if not raw_input_path:
                continue
                
            working_path, original_filename, original_parent_dir = get_real_path_or_copy(raw_input_path, cache_dir)
            
            if not working_path or working_path.startswith("content://"):
                self.write_log(f"[ERROR] ファイルの取得・コピーに失敗しました: {raw_input_path}")
                continue

            try:
                if original_parent_dir and os.path.exists(original_parent_dir):
                    target_out_dir = os.path.join(original_parent_dir, "PapaAlbum")
                elif os.path.exists(dcim_dir):
                    target_out_dir = os.path.join(dcim_dir, "PapaAlbum")
                elif os.path.exists(pictures_dir):
                    target_out_dir = os.path.join(pictures_dir, "PapaAlbum")
                else:
                    target_out_dir = os.path.join(download_dir, "PapaAlbum")

                os.makedirs(target_out_dir, exist_ok=True)

                filename = original_filename if original_filename else pathlib.Path(working_path).name
                ext = pathlib.Path(filename).suffix.lower()
                
                output_path = get_unique_target_path(target_out_dir, filename)
                
                try:
                    fallback_mtime = os.path.getmtime(working_path)
                except Exception:
                    fallback_mtime = time.time()
                
                # --- 画像圧縮 & Exif（位置情報・GPS等）継承 ---
                if ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    self.write_log(f"[PROCESSING] 画像圧縮中 ({pathlib.Path(output_path).name})")
                    
                    exif_bytes = None
                    if ext in [".jpg", ".jpeg"]:
                        try:
                            exif_dict = piexif.load(working_path)
                            if "0th" in exif_dict and piexif.ImageIFD.Orientation in exif_dict["0th"]:
                                exif_dict["0th"][piexif.ImageIFD.Orientation] = 1
                            exif_bytes = piexif.dump(exif_dict)
                        except Exception as e:
                            self.write_log(f"[INFO] Exif抽出・補正スキップ: {e}")

                    with Image.open(working_path) as img:
                        target_mtime = get_exif_mtime(img, fallback_mtime)
                        img = ImageOps.exif_transpose(img)
                        img.thumbnail((3000, 3000))
                        
                        save_kwargs = {"optimize": True}
                        if ext in [".jpg", ".jpeg"]:
                            save_kwargs["quality"] = 85
                            if exif_bytes:
                                save_kwargs["exif"] = exif_bytes

                        img.save(output_path, **save_kwargs)
                    
                    try:
                        os.utime(output_path, (target_mtime, target_mtime))
                    except Exception as e:
                        self.write_log(f"[WARNING] 日付設定失敗: {e}")
                        
                    img_count += 1
                    self.write_log(f"[SUCCESS] 保存完了: {output_path}")
                    
                # --- 動画処理 (AV1圧縮 or 直接コピー) ---
                elif ext in [".mp4", ".mov", ".m4v"]:
                    self.write_log(f"[PROCESSING] AV1動画圧縮中: {pathlib.Path(output_path).name}")
                    try:
                        compress_video_av1(working_path, output_path)
                        self.write_log(f"[SUCCESS] AV1圧縮完了: {output_path}")
                    except Exception as video_err:
                        self.write_log(f"[WARNING] AV1スキップ(コピーへ移行): {video_err}")
                        shutil.copy2(working_path, output_path)
                        self.write_log(f"[SUCCESS] コピー完了: {output_path}")

                    try:
                        os.utime(output_path, (fallback_mtime, fallback_mtime))
                    except Exception:
                        pass

                    video_count += 1
                    
                else:
                    self.write_log(f"[SKIP] 未対応フォーマット: {filename} ({ext})")
                    
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
            result_text = f"スッキリ完了！\n画像 {img_count}枚 / 動画 {video_count}本 を整理しました！\n/PapaAlbum フォルダ等に保存されました。"
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
        load_native_libraries()
        init_ffmpeg_path()  # メインスレッド上でFFmpegパスを初期化

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