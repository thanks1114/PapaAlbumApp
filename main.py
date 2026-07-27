import os
import subprocess
from kivy.utils import platform

def test_native_libraries():
    """
    Android上でネイティブライブラリ(.so)のロードおよび
    FFmpegバイナリの起動が可能かを単体テストする
    """
    print("=" * 40)
    print(" Native Library Standalone Test ")
    print("=" * 40)
    
    if platform != "android":
        print("[INFO] Android環境ではありません。PC環境での実行をスキップします。")
        return

    try:
        from jnius import autoclass
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        System = autoclass('java.lang.System')
        
        activity = PythonActivity.mActivity
        lib_dir = activity.getApplicationInfo().nativeLibraryDir
        print(f"[INFO] Native Library Directory:\n  -> {lib_dir}\n")

        # -------------------------------------------------------------
        # テスト 1: C/C++ 共有ライブラリ (.so) の Java 側ロード確認
        # -------------------------------------------------------------
        print("--- [TEST 1] System.loadLibrary チェック ---")
        libs_to_test = [
            "SvtAv1Enc",
            "avutil",
            "swresample",
            "avcodec",
            "swscale",
            "avformat",
            "avfilter"
        ]

        for lib in libs_to_test:
            try:
                System.loadLibrary(lib)
                print(f"  [SUCCESS] lib{lib}.so : ロード成功")
            except Exception as e:
                print(f"  [FAILED]  lib{lib}.so : ロード失敗 -> {e}")

        # -------------------------------------------------------------
        # テスト 2: libffmpeg.so バイナリの実行可否確認 (-version)
        # -------------------------------------------------------------
        print("\n--- [TEST 2] FFmpeg バイナリ起動テスト (-version) ---")
        ffmpeg_so = os.path.join(lib_dir, "libffmpeg.so")
        
        if not os.path.exists(ffmpeg_so):
            print(f"  [FAILED] {ffmpeg_so} が見つかりません。")
            return

        try:
            os.chmod(ffmpeg_so, 0o755)
        except Exception as e:
            print(f"  [WARNING] os.chmod 失敗: {e}")

        env = os.environ.copy()
        env["LD_LIBRARY_PATH"] = lib_dir

        # FFmpegのバージョン情報を取得するだけのコマンド
        cmd = [ffmpeg_so, "-version"]
        
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
            first_line = stdout.splitlines()[0] if stdout else "Output is empty"
            print(f"  [SUCCESS] FFmpeg 起動成功！")
            print(f"  -> バージョン情報: {first_line}")
        else:
            print(f"  [FAILED] FFmpeg 異常終了 (Return code: {process.returncode})")
            if stderr:
                print(f"  -> エラー詳細:\n{stderr.strip()[:300]}")

    except Exception as e:
        print(f"\n[CRITICAL ERROR] テスト全体で例外が発生しました: {e}")

    print("\n" + "=" * 40)
    print(" テスト完了 ")
    print("=" * 40)


if __name__ == "__main__":
    test_native_libraries()