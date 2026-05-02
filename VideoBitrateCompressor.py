import os
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

VIDEO_EXTS = (".mp4", ".mov", ".mkv", ".avi")

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Video CRF Compressor")

        self.input_dir = tk.StringVar()
        self.crf = tk.IntVar(value=23)
        self.preset = tk.StringVar(value="medium")

        # ===== 入力フォルダ =====
        tk.Label(root, text="入力フォルダ").pack(anchor="w")
        frame = tk.Frame(root)
        frame.pack(fill="x")

        tk.Entry(frame, textvariable=self.input_dir).pack(side="left", fill="x", expand=True)
        tk.Button(frame, text="参照", command=self.select_folder).pack(side="right")

        # ===== CRFスライダー =====
        tk.Label(root, text="品質（CRF）").pack(anchor="w")

        self.slider = tk.Scale(
            root,
            from_=18,
            to=28,
            orient="horizontal",
            resolution=1,
            variable=self.crf
        )
        self.slider.pack(fill="x")

        self.crf_label = tk.Label(root, text="CRF 23（標準）")
        self.crf_label.pack()

        self.slider.bind("<Motion>", self.update_label)

        # ===== preset選択 =====
        tk.Label(root, text="圧縮速度 / 効率").pack(anchor="w")

        preset_frame = tk.Frame(root)
        preset_frame.pack()

        presets = ["fast", "medium", "slow"]
        for p in presets:
            tk.Radiobutton(preset_frame, text=p, value=p, variable=self.preset).pack(side="left")

        # ===== 開始ボタン =====
        tk.Button(root, text="開始", command=self.start).pack(pady=5)

        # ===== ログ =====
        tk.Label(root, text="ログ").pack(anchor="w")
        self.log = scrolledtext.ScrolledText(root, height=15)
        self.log.pack(fill="both", expand=True)

    def update_label(self, event=None):
        value = self.crf.get()
        text = f"CRF {value}"

        if value <= 20:
            text += "（高画質）"
        elif value <= 24:
            text += "（標準）"
        else:
            text += "（容量優先）"

        self.crf_label.config(text=text)

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.input_dir.set(folder)

    def log_write(self, text):
        self.log.insert(tk.END, text + "\n")
        self.log.see(tk.END)
        self.root.update()

    def start(self):
        input_dir = self.input_dir.get()

        if not os.path.isdir(input_dir):
            messagebox.showerror("エラー", "フォルダを選択してください")
            return

        output_dir = os.path.join(input_dir, "compressed")
        os.makedirs(output_dir, exist_ok=True)

        crf = self.crf.get()
        preset = self.preset.get()

        for file in os.listdir(input_dir):
            if not file.lower().endswith(VIDEO_EXTS):
                continue

            if "_compressed" in file:
                self.log_write(f"スキップ（圧縮済み）: {file}")
                continue

            input_path = os.path.join(input_dir, file)
            name, _ = os.path.splitext(file)
            output_path = os.path.join(output_dir, f"{name}_compressed.mp4")

            if os.path.exists(output_path):
                self.log_write(f"スキップ（既に存在）: {file}")
                continue

            self.log_write(f"処理開始: {file}")

            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-c:v", "libx264",
                "-crf", str(crf),
                "-preset", preset,
                "-c:a", "aac",
                "-b:a", "128k",
                "-y",
                output_path
            ]

            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                self.log_write(f"完了: {file}")
            except Exception as e:
                self.log_write(f"失敗: {file} | {e}")

        self.log_write("=== 全処理終了 ===")


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()