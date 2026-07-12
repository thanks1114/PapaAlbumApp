from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.properties import StringProperty

from ffmpeg_kit import FFmpegKit
from ffmpeg_kit import ReturnCode

from androidstorage4kivy import SharedStorage
from PIL import Image
import piexif
import os
import pathlib
from datetime import datetime


class RootWidget(BoxLayout):
    log_text = StringProperty("ファイルを選択してください")

    def __init__(self, **kwargs):
        super().__init__(orientation="vertical", **kwargs)

        btn_select = Button(text="ファイルを選択", size_hint_y=None, height=60)
        btn_select.bind(on_press=self.select_file)
        self.add_widget(btn_select)

        btn_compress = Button(text="圧縮する", size_hint_y=None, height=60)
        btn_compress.bind(on_press=self.compress_file)
        self.add_widget(btn_compress)

        self.log_label = Label(text=self.log_text)
        self.add_widget(self.log_label)

        self.selected_file = None

    def select_file(self, instance):
        ss = SharedStorage()
        uri = ss.open_file()
        if uri:
            self.selected_file = ss.copy_from_shared(uri)
            self.log_text = f"選択: {self.selected_file}"
            self.log_label.text = self.log_text

    def compress_file(self, instance):
        if not self.selected_file:
            self.log_text = "ファイルが選択されていません"
            self.log_label.text = self.log_text
            return

        path = self.selected_file
        root, ext = os.path.splitext(path)
        output_path = root + "_PapaAlbum" + ext

        ext = ext.lower()

        if ext in [".jpg", ".jpeg", ".png", ".webp"]:
            self.compress_image(path, output_path)
        elif ext in [".mp4", ".mov", ".mkv", ".webm"]:
            self.compress_video(path, output_path)
        else:
            self.log_text = "対象外の拡張子です"
            self.log_label.text = self.log_text

    def compress_image(self, input_path, output_path):
        img = Image.open(input_path)

        exif_dict = None
        if "exif" in img.info:
            exif_dict = piexif.load(img.info["exif"])

        w, h = img.size
        long_side = 3000
        scale = long_side / max(w, h)

        if 0 < scale < 1:
            img = img.resize((int(w * scale), int(h * scale)))

        exif_bytes = b""
        if exif_dict:
            if "thumbnail" in exif_dict:
                del exif_dict["thumbnail"]
            exif_bytes = piexif.dump(exif_dict)

        img.save(output_path, exif=exif_bytes)

        self.log_text = f"画像圧縮成功: {output_path}"
        self.log_label.text = self.log_text

    def compress_video(self, input_path, output_path):
        long_side = 3840
        crf = 22

        cmd = (
            f"-y -i '{input_path}' "
            f"-vf scale='if(gt(max(iw,ih),{long_side}),if(gt(iw,ih),{long_side},-1),iw)':"
            f"'if(gt(max(iw,ih),{long_side}),if(gt(ih,iw),{long_side},-1),ih)' "
            f"-c:v libsvtav1 -crf {crf} -preset 8 "
            f"-c:a aac '{output_path}'"
        )

        session = FFmpegKit.execute(cmd)

        if session.get_return_code().is_value_success():
            self.log_text = f"動画圧縮成功: {output_path}"
        else:
            self.log_text = "動画圧縮失敗"

        self.log_label.text = self.log_text


class PapaAlbumApp(App):
    def build(self):
        return RootWidget()


if __name__ == "__main__":
    PapaAlbumApp().run()
