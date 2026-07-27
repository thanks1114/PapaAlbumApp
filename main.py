import os
import subprocess
from kivy.utils import platform

def compress_video(input_path: str, output_path: str) -> bool:
    """
    指定された動画ファイルをFFmpegで圧縮する（スレッドなしの同期処理）
    
    :param input_path: 圧縮元の動画ファイルパス
    :param output_path: 圧縮後の保存先パス
    :return: 成功したら True, 失敗したら False
    """
    ffmpeg_path = "ffmpeg"
    env = os.environ.copy()

    # Android実機で動作させる場合のライブラリパス設定
    if platform == "android":
        try:
            from jnius import autoclass
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            lib_dir = PythonActivity.mActivity.getApplicationInfo().nativeLibraryDir
            
            ffmpeg_so = os.path.join(lib_dir, "libffmpeg.so")
            if os.path.exists(ffmpeg_so):
                ffmpeg_path = ffmpeg_so
                try:
                    os.chmod(ffmpeg_so, 0o755)
                except Exception:
                    pass
            
            env["LD_LIBRARY_PATH"] = lib_dir
        except Exception as e:
            print(f"[ERROR] Android環境の初期化失敗: {e}")

    # FFmpegコマンド設定
    # ※ AV1以外のH.264などに変更したい場合は -vcodec を "libx264" に変更してください
    cmd = [
        ffmpeg_path, "-y",
        "-i", input_path,
        "-vcodec", "libsvtav1",
        "-crf", "38",
        "-preset", "12",
        "-acodec", "aac",
        "-b:a", "128k",
        "-movflags", "+faststart",
        output_path
    ]

    print(f"[START] 動画圧縮を開始します: {input_path}")

    # スレッドを使わず、その場でプロセスを実行して完了まで待機
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        text=True,
        errors='ignore'
    )
    
    stdout, stderr = process.communicate()

    if process.returncode == 0:
        print(f"[SUCCESS] 圧縮完了: {output_path}")
        return True
    else:
        err_msg = stderr.strip() if stderr else f"Return code: {process.returncode}"
        print(f"[ERROR] 圧縮失敗 (code {process.returncode}): {err_msg[-300:]}")
        return False


# --- 使用例 ---
if __name__ == "__main__":
    # 処理したい動画のパスを指定
    src_video = "/storage/emulated/0/DCIM/Camera/PXL_20260725_010437613.mp4"
    dst_video = "/storage/emulated/0/DCIM/PapaAlbum/sample_compressed.mp4"

    if os.path.exists(src_video):
        compress_video(src_video, dst_video)
    else:
        print(f"ファイルが存在しません: {src_video}")