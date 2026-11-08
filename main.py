
import queue
import threading
import tkinter as tk
import webbrowser
import sys

from pathlib import Path
from tkinter import filedialog, messagebox

from auth import authorize, connect, get_token
from app_info import APP_WINDOW_TITLE
from exporter import export_liked_tracks


class MusicExporterApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_WINDOW_TITLE)
        self.geometry("580x360")
        self.minsize(500, 340)
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)
        else:
            base_path = Path(__file__).resolve().parent

        self.iconbitmap(str(base_path / "assets" / "icon.ico"))

        self.events = queue.Queue()
        self.auth_window = None

        self.output_path = tk.StringVar(
            value=str(Path.home() / "Documents" / "Любимые песни.md")
        )
        self.status = tk.StringVar(value="Готово к работе")

        self.create_widgets()
        self.after(100, self.process_events)

    def create_widgets(self):
        container = tk.Frame(self, padx=20, pady=20)
        container.pack(fill="both", expand=True)

        tk.Label(
            container,
            text="Выгрузка любимых песен",
            font=("Segoe UI", 16, "bold")
        ).pack(anchor="w", pady=(0, 20))

        self.auth_button = tk.Button(
            container,
            text="Подключить Яндекс",
            command=self.start_auth
        )
        self.auth_button.pack(fill="x", pady=(0, 18))

        tk.Label(
            container,
            text="Путь к заметке Markdown:"
        ).pack(anchor="w")

        path_frame = tk.Frame(container)
        path_frame.pack(fill="x", pady=(6, 20))

        tk.Entry(
            path_frame,
            textvariable=self.output_path
        ).pack(side="left", fill="x", expand=True)

        tk.Button(
            path_frame,
            text="Обзор...",
            command=self.select_output
        ).pack(side="left", padx=(8, 0))

        self.export_button = tk.Button(
            container,
            text="Выгрузить любимые песни",
            command=self.export_music,
            height=2
        )
        self.export_button.pack(fill="x")

        tk.Label(
            container,
            textvariable=self.status,
            anchor="w",
            fg="gray"
        ).pack(side="bottom", fill="x")

        if get_token():
            self.status.set("Данные авторизации сохранены")

    def select_output(self):
        path = filedialog.asksaveasfilename(
            title="Выберите файл заметки",
            defaultextension=".md",
            filetypes=[("Markdown", "*.md")],
            initialfile="Любимые песни.md"
        )

        if path:
            self.output_path.set(path)

    def start_auth(self):
        self.auth_button.config(state="disabled")
        self.status.set("Ожидание ответа Яндекса...")

        threading.Thread(
            target=self.auth_worker,
            daemon=True
        ).start()

    def auth_worker(self):
        try:
            def on_code(code):
                self.events.put((
                    "code",
                    code.user_code,
                    code.verification_url
                ))

            authorize(on_code)
            self.events.put(("success",))

        except Exception as error:
            self.events.put(("error", str(error)))

    def show_auth_window(self, user_code, url):
        self.auth_window = tk.Toplevel(self)
        self.auth_window.title("Подключение Яндекса")
        self.auth_window.geometry("430x220")
        self.auth_window.resizable(False, False)

        tk.Label(
            self.auth_window,
            text="Введите этот код на странице Яндекса:",
            font=("Segoe UI", 11)
        ).pack(pady=(20, 10))

        tk.Label(
            self.auth_window,
            text=user_code,
            font=("Segoe UI", 22, "bold")
        ).pack(pady=5)

        tk.Button(
            self.auth_window,
            text="Открыть страницу подтверждения",
            command=lambda: webbrowser.open(url)
        ).pack(pady=15)

        tk.Label(
            self.auth_window,
            text="Ожидаем подтверждения входа...",
            fg="gray"
        ).pack()

    def process_events(self):
        try:
            while True:
                event = self.events.get_nowait()
                event_type = event[0]

                if event_type == "code":
                    self.show_auth_window(event[1], event[2])
                    self.status.set("Подтвердите вход в браузере")

                elif event_type == "success":
                    self.auth_button.config(state="normal")
                    self.status.set("Учётная запись подключена")

                    if self.auth_window:
                        self.auth_window.destroy()
                        self.auth_window = None

                    messagebox.showinfo(
                        "Успешно",
                        "Авторизация завершена!"
                    )

                elif event_type == "error":
                    self.auth_button.config(state="normal")
                    self.status.set("Ошибка авторизации")

                    if self.auth_window:
                        self.auth_window.destroy()
                        self.auth_window = None

                    messagebox.showerror(
                        "Ошибка",
                        event[1]
                    )


                elif event_type == "export_success":
                    self.export_button.config(state="normal")
                    self.status.set(
                        f"Выгружено композиций: {event[1]}"
                    )

                    messagebox.showinfo(
                        "Выгрузка завершена",
                        f"Композиции: {event[1]}\n"
                        f"Группы исполнителей: {event[2]}"
                    )

                elif event_type == "export_error":
                    self.export_button.config(state="normal")
                    self.status.set("Ошибка выгрузки")

                    messagebox.showerror(
                        "Ошибка выгрузки",
                        event[1]
                    )


        except queue.Empty:
            pass

        self.after(100, self.process_events)

    
    def export_music(self):
        if not get_token():
            messagebox.showwarning(
                "Нет подключения",
                "Сначала подключите учётную запись Яндекса."
            )
            return

        output_path = self.output_path.get().strip()

        if not output_path:
            messagebox.showwarning(
                "Не указан путь",
                "Выберите файл для сохранения заметки."
            )
            return

        self.export_button.config(state="disabled")
        self.status.set("Получение любимых композиций...")

        threading.Thread(
            target=self.export_worker,
            args=(output_path,),
            daemon=True
        ).start()

    def export_worker(self, output_path):
        try:
            total, artists = export_liked_tracks(output_path)
            self.events.put(("export_success", total, artists))
        except Exception as error:
            self.events.put(("export_error", str(error)))



if __name__ == "__main__":
    app = MusicExporterApp()
    app.mainloop()
