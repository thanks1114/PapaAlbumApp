import os
import sys
from kivy.utils import platform


def compress_video(input_path: str, output_path: str) -> bool:
    """指定された動画ファイルをFFmpegKit(Android)で圧縮する（同期処理）

    :param input_path: 圧縮元の動画ファイルパス
    :param output_path: 圧縮後の保存先パス
    :return: 成功したら True, 失敗したら False
    """
    print(f"[START] 動画圧縮を開始します: {input_path}")

    # 出力先ディレクトリが存在しない場合は作成
    out_dir = os.path.dirname(output_path)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # --- Android実機環境での処理 ---
    if platform == "android":
        try:
            from jnius import autoclass

            # FFmpegKit Javaクラスの取得
            FFmpegKit = autoclass("com.arthenica.ffmpegkit.FFmpegKit")
            ReturnCode = autoclass("com.arthenica.ffmpegkit.ReturnCode")

            # コマンド引数の組み立て (配列ではなく文字列で指定)
            command = (
                f'-y -i "{input_path}" '
                f"-vcodec libsvtav1 -crf 38 -preset 12 "
                f'-acodec aac -b:a 128k -movflags +faststart "{output_path}"'
            )

            # FFmpegKit の実行（完了までブロッキング同期処理）
            session = FFmpegKit.execute(command)
            return_code = session.getReturnCode()

            # 実行結果の確認
            if ReturnCode.isSuccess(return_code):
                print(f"[SUCCESS] 圧縮完了: {output_path}")
                return True
            else:
                fail_trace = session.getFailStackTrace()
                output = session.getOutput()
                err_msg = output or fail_trace or f"Return code: {return_code}"
                print(
                    f"[ERROR] 圧縮失敗 (code {return_code}): {str(err_msg)[-300:]}"
                )
                return False

        except Exception as e:
            import traceback

            print(
                f"[ERROR] Android環境でのFFmpegKit実行失敗:\n{traceback.format_exc()}"
            )
            return False

    # --- PC環境（開発・テスト用）のフォールバック処理 ---
    else:
        import subprocess

        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            input_path,
            "-vcodec",
            "libsvtav1",
            "-crf",
            "38",
            "-preset",
            "12",
            "-acodec",
            "aac",
            "-b:a",
            "128k",
            "-movflags",
            "+faststart",
            output_path,
        ]

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                errors="ignore",
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                print(f"[SUCCESS] 圧縮完了: {output_path}")
                return True
            else:
                err_msg = (
                    stderr.strip()
                    if stderr
                    else f"Return code: {process.returncode}"
                )
                print(
                    f"[ERROR] 圧縮失敗 (code {process.returncode}): {err_msg[-300:]}"
                )
                return False
        except Exception as e:
            print(f"[ERROR] PC環境での実行失敗: {e}")
            return False


# --- 使用例 ---
if __name__ == "__main__":
    src_video = "/storage/emulated/0/DCIM/Camera/PXL_20260725_010437613.mp4"
    dst_video = "/storage/emulated/0/DCIM/PapaAlbum/sample_compressed.mp4"

    if os.path.exists(src_video):
        compress_video(src_video, dst_video)
    else:
        print(f"ファイルが存在しません: {src_video}")