import os
import json
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi")
SETTINGS_FILE = "settings.json"


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video CRF Compressor")

        self.input_dir = tk.StringVar()
        self.quality = tk.IntVar(value=23)
        self.preset = tk.StringVar(value="medium")
        self.encoder = tk.StringVar(value="CPU (libx264)")
        self.is_running = False

        tk.Label(root, text="入力フォルダ").pack(anchor="w")
        frame = tk.Frame(root)
        frame.pack(fill="x")

        tk.Entry(frame, textvariable=self.input_dir).pack(side="left", fill="x", expand=True)
        tk.Button(frame, text="参照", command=self.select_folder).pack(side="right")

        tk.Label(root, text="エンコード方式").pack(anchor="w")
        tk.OptionMenu(
            root,
            self.encoder,
            "CPU (libx264)",
            "GPU (NVIDIA NVENC)"
        ).pack(fill="x")

        tk.Label(root, text="品質（CPU: CRF / GPU: CQ）").pack(anchor="w")

        self.slider = tk.Scale(
            root,
            from_=18,
            to=36,
            orient="horizontal",
            resolution=1,
            variable=self.quality,
            command=lambda value: self.update_label()
        )
        self.slider.pack(fill="x")

        self.quality_label = tk.Label(root, text="品質 23（標準）")
        self.quality_label.pack()

        tk.Label(root, text="CPU圧縮速度 / 効率").pack(anchor="w")
        preset_frame = tk.Frame(root)
        preset_frame.pack()

        for p in ["veryfast", "fast", "medium", "slow"]:
            tk.Radiobutton(
                preset_frame,
                text=p,
                value=p,
                variable=self.preset
            ).pack(side="left")

        self.start_button = tk.Button(root, text="開始", command=self.start)
        self.start_button.pack(pady=5)

        self.open_button = tk.Button(
            root,
            text="出力フォルダを開く",
            command=self.open_output_folder
        )
        self.open_button.pack(pady=3)

        self.current_file_label = tk.Label(root, text="現在のファイル：なし")
        self.current_file_label.pack(anchor="w")

        tk.Label(root, text="現在の動画の進捗").pack(anchor="w")
        self.file_progress = ttk.Progressbar(root, maximum=100)
        self.file_progress.pack(fill="x", padx=5)

        self.file_progress_label = tk.Label(root, text="0%")
        self.file_progress_label.pack(anchor="w")

        tk.Label(root, text="全体の進捗").pack(anchor="w")
        self.total_progress = ttk.Progressbar(root, maximum=100)
        self.total_progress.pack(fill="x", padx=5)

        self.total_progress_label = tk.Label(root, text="0%")
        self.total_progress_label.pack(anchor="w")

        tk.Label(root, text="ログ").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(root, height=12)
        self.log.pack(fill="both", expand=True)

        self.load_settings()
        self.update_label()

        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def open_output_folder(self):
        input_dir = self.input_dir.get()

        if not os.path.isdir(input_dir):
            return

        output_dir = os.path.join(input_dir, "compressed")

        if os.path.exists(output_dir):
            os.startfile(output_dir)
        else:
            messagebox.showinfo("情報", "まだ出力フォルダが作成されていません")

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            return

        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                settings = json.load(f)

            self.input_dir.set(settings.get("input_dir", ""))
            self.encoder.set(settings.get("encoder", "CPU (libx264)"))
            self.quality.set(settings.get("quality", 23))
            self.preset.set(settings.get("cpu_preset", "medium"))

        except Exception:
            pass

    def save_settings(self):
        settings = {
            "input_dir": self.input_dir.get(),
            "encoder": self.encoder.get(),
            "quality": self.quality.get(),
            "cpu_preset": self.preset.get()
        }

        try:
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(settings, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def on_close(self):
        self.save_settings()
        self.root.destroy()

    def update_label(self):
        value = self.quality.get()

        if value <= 20:
            level = "高画質"
        elif value <= 24:
            level = "標準"
        elif value <= 28:
            level = "容量優先"
        else:
            level = "かなり軽量"

        self.quality_label.config(text=f"品質 {value}（{level}）")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_dir.set(folder)
            self.save_settings()

    def log_write(self, text):
        self.root.after(0, self._log_write_main_thread, text)

    def _log_write_main_thread(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)

    def set_running_state(self, running):
        self.root.after(0, self._set_running_state_main_thread, running)

    def _set_running_state_main_thread(self, running):
        self.is_running = running
        self.start_button.config(state="disabled" if running else "normal")

    def set_current_file(self, filename):
        self.root.after(
            0,
            lambda: self.current_file_label.config(text=f"現在のファイル：{filename}")
        )

    def update_file_progress(self, percent):
        self.root.after(0, self._update_file_progress_main_thread, percent)

    def _update_file_progress_main_thread(self, percent):
        percent = max(0, min(100, percent))
        self.file_progress["value"] = percent
        self.file_progress_label.config(text=f"{percent:.1f}%")

    def update_total_progress(self, percent):
        self.root.after(0, self._update_total_progress_main_thread, percent)

    def _update_total_progress_main_thread(self, percent):
        percent = max(0, min(100, percent))
        self.total_progress["value"] = percent
        self.total_progress_label.config(text=f"{percent:.1f}%")

    def start(self):
        if self.is_running:
            return

        input_dir = self.input_dir.get()

        if not os.path.isdir(input_dir):
            messagebox.showerror("エラー", "フォルダを選択してください")
            return

        self.save_settings()
        self.set_running_state(True)

        thread = threading.Thread(
            target=self.compress_videos,
            args=(
                input_dir,
                self.quality.get(),
                self.preset.get(),
                self.encoder.get()
            ),
            daemon=True
        )
        thread.start()

    def get_duration_seconds(self, input_path):
        cmd = [
            "ffprobe",
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            input_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            return None

        try:
            return float(result.stdout.strip())
        except ValueError:
            return None

    def build_ffmpeg_command(self, input_path, output_path, quality, cpu_preset, encoder):
        if encoder == "GPU (NVIDIA NVENC)":
            return [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-i", input_path,
                "-c:v", "h264_nvenc",
                "-cq", str(quality),
                "-preset", "p4",
                "-c:a", "aac",
                "-b:a", "128k",
                "-progress", "pipe:1",
                "-nostats",
                output_path
            ]

        return [
            "ffmpeg",
            "-hide_banner",
            "-y",
            "-i", input_path,
            "-c:v", "libx264",
            "-crf", str(quality),
            "-preset", cpu_preset,
            "-c:a", "aac",
            "-b:a", "128k",
            "-progress", "pipe:1",
            "-nostats",
            output_path
        ]

    def compress_videos(self, input_dir, quality, cpu_preset, encoder):
        output_dir = os.path.join(input_dir, "compressed")
        os.makedirs(output_dir, exist_ok=True)

        files = [
            file for file in os.listdir(input_dir)
            if file.lower().endswith(VIDEO_EXTS)
            and "_compressed" not in file
        ]

        if not files:
            self.log_write("対象動画がありません。")
            self.set_current_file("なし")
            self.set_running_state(False)
            return

        total_files = len(files)
        completed_files = 0

        self.log_write("=== 処理開始 ===")
        self.log_write(f"Encoder: {encoder}")
        self.log_write(f"Quality: {quality}")
        self.log_write(f"CPU Preset: {cpu_preset}")
        self.log_write(f"出力先: {output_dir}")

        for file in files:
            input_path = os.path.join(input_dir, file)
            name, _ = os.path.splitext(file)
            output_path = os.path.join(output_dir, f"{name}_compressed.mp4")

            self.set_current_file(file)
            self.update_file_progress(0)

            if os.path.exists(output_path):
                self.log_write(f"スキップ（既に存在）: {file}")
                completed_files += 1
                self.update_total_progress(completed_files / total_files * 100)
                continue

            duration = self.get_duration_seconds(input_path)

            if duration is None or duration <= 0:
                self.log_write(f"動画時間を取得できませんでした: {file}")

            self.log_write(f"処理開始: {file}")

            cmd = self.build_ffmpeg_command(
                input_path,
                output_path,
                quality,
                cpu_preset,
                encoder
            )

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )

                last_lines = []

                while True:
                    line = process.stdout.readline()

                    if line == "" and process.poll() is not None:
                        break

                    if not line:
                        continue

                    line = line.strip()

                    if line:
                        last_lines.append(line)
                        if len(last_lines) > 20:
                            last_lines.pop(0)

                    if line.startswith("out_time_ms=") and duration:
                        try:
                            out_time_ms = int(line.split("=")[1])
                            current_seconds = out_time_ms / 1_000_000
                            percent = current_seconds / duration * 100
                            self.update_file_progress(percent)
                        except ValueError:
                            pass

                returncode = process.wait()

                if returncode == 0:
                    self.update_file_progress(100)
                    self.log_write(f"完了: {file}")
                else:
                    self.log_write(f"失敗: {file}")
                    self.log_write("---- ffmpegログ末尾 ----")
                    for log_line in last_lines:
                        self.log_write(log_line)

            except Exception as e:
                self.log_write(f"失敗: {file} | {e}")

            completed_files += 1
            self.update_total_progress(completed_files / total_files * 100)

        self.set_current_file("なし")
        self.log_write("=== 全処理終了 ===")
        self.set_running_state(False)


if __name__ == "__main__":
    root = tk.Tk()
    root.geometry("720x620")
    app = App(root)
    root.mainloop()