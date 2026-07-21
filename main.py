import os
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.storage.jsonstore import JsonStore
from kivy.core.text import LabelBase
from kivy.utils import platform

from PIL import Image, ImageOps
import piexif

# --- 日本語フォントの安全なフォールバック設定 ---
FONT_NAME = "Roboto"
if platform == "win":
    win_font = r"C:\Windows\Fonts\msgothic.ttc"
    if os.path.exists(win_font):
        LabelBase.register(name=FONT_NAME, fn_regular=win_font)

# --- pillow-heif の安全なガード読み込み ---
HEIF_SUPPORTED = False
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
    HEIF_SUPPORTED = True
    print("pillow-heif loaded successfully")
except Exception as e:
    # Android(ARM64)環境等でCライブラリの読み込みに失敗してもアプリは起動させる
    print(f"pillow-heif not available, fallback to default Pillow: {e}")


def process_image_with_exif(src_path, dst_path, max_size=(1920, 1920), quality=85):
    """
    位置情報(GPS)・日時を保持し、
    回転を直立に補正してJPEG保存する関数
    """
    try:
        with Image.open(src_path) as img:
            # 1. 元のExifデータを取得
            exif_bytes = img.info.get('exif')

            # 2. Exifの回転情報を反映して画像を正しい向きに回転
            img = ImageOps.exif_transpose(img)

            # 3. アスペクト比を維持してリサイズ
            img.thumbnail(max_size, Image.Resampling.LANCZOS)

            # 4. 二重回転を防止するため、Exif内の Orientation タグを 1 (正常) に更新
            if exif_bytes:
                try:
                    exif_dict = piexif.load(exif_bytes)
                    exif_dict['0th'][piexif.ImageIFD.Orientation] = 1
                    exif_bytes = piexif.dump(exif_dict)
                except Exception as e:
                    print(f"Exif piexif update skipped: {e}")

            # 5. JPEG保存用にモード変換 (RGBA -> RGB)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # 6. Exif付きで保存
            if exif_bytes:
                img.save(dst_path, "JPEG", quality=quality, exif=exif_bytes)
            else:
                img.save(dst_path, "JPEG", quality=quality)
        return True
    except Exception as e:
        print(f"Image processing error: {e}")
        return False


class PapaAlbumApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.status_label = Label(text="アプリが正常に起動しました", font_name=FONT_NAME)
        self.layout.add_widget(self.status_label)
        return self.layout

    def on_start(self):
        # 設定の読み込み
        self.store = JsonStore('papaalbum_settings.json')
        
        # Android 権限リクエスト (Android 13/14/15 対応)
        if platform == "android":
            try:
                from android.permissions import request_permissions, Permission
                request_permissions([
                    Permission.READ_EXTERNAL_STORAGE,
                    Permission.WRITE_EXTERNAL_STORAGE,
                    Permission.READ_MEDIA_IMAGES,
                    Permission.READ_MEDIA_VIDEO
                ])
            except Exception as e:
                print(f"Permission request error: {e}")


if __name__ == '__main__':
    PapaAlbumApp().run()