
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import tkinter.font as tkfont
import subprocess
import tempfile
import threading
import os
import sys
import time
import re

# OpenAI is optional until you use the AI assistant.
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ---------------- CONFIGURATION ----------------

BG = "#1e1e1e"
PANEL = "#252526"
EDITOR_BG = "#1e1e1e"
FG = "#d4d4d4"
ACCENT = "#007acc"
GREEN = "#4ec9b0"
YELLOW = "#dcdcaa"
PURPLE = "#c586c0"
BLUE = "#569cd6"
ORANGE = "#ce9178"

MODEL = "gpt-5.5"


class PythonWorkspace:

    def __init__(self, root):
        self.root = root
        self.root.title("Python Workspace 1.0")
        self.root.geometry("1200x760")
        self.root.minsize(850, 550)
        self.root.configure(bg=BG)

        self.current_file = None
        self.start_time = None
        self.elapsed = 0
        self.running = False

        self.build_interface()
        self.update_clock()
        self.update_stopwatch()
        self.update_line_numbers()

        self.editor.bind("<KeyRelease>", self.on_editor_change)
        self.editor.bind("<MouseWheel>", self.sync_scroll)
        self.editor.bind("<Button-1>", self.update_cursor_position)

        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<F5>", lambda e: self.run_code())

        self.insert_welcome_code()

    # ---------------- INTERFACE ----------------

    def build_interface(self):

        # Top navigation
        top = tk.Frame(self.root, bg="#333333", height=45)
        top.pack(fill="x")

        tk.Label(
            top, text="  PYTHON WORKSPACE",
            bg="#333333", fg="white",
            font=("Arial", 12, "bold")
        ).pack(side="left", padx=10, pady=10)

        self.clock_label = tk.Label(
            top, bg="#333333", fg=GREEN,
            font=("Consolas", 10)
        )
        self.clock_label.pack(side="right", padx=15)

        # Toolbar
        toolbar = tk.Frame(self.root, bg=PANEL)
        toolbar.pack(fill="x")

        buttons = [
            ("New", self.new_file),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("▶ Run", self.run_code),
            ("Clear Output", self.clear_output),
        ]

        for label, command in buttons:
            tk.Button(
                toolbar, text=label,
                command=command,
                bg="#3c3c3c", fg="white",
                activebackground=ACCENT,
                activeforeground="white",
                relief="flat", padx=12, pady=7
            ).pack(side="left", padx=3, pady=5)

        # Main workspace
        main = tk.PanedWindow(
            self.root, orient="horizontal",
            bg=BG, sashwidth=5
        )
        main.pack(fill="both", expand=True)

        # Editor panel
        editor_frame = tk.Frame(main, bg=EDITOR_BG)
        main.add(editor_frame, width=780)

        editor_header = tk.Frame(editor_frame, bg=PANEL)
        editor_header.pack(fill="x")

        self.file_label = tk.Label(
            editor_header, text="  untitled.py",
            bg=PANEL, fg=FG,
            font=("Arial", 10)
        )
        self.file_label.pack(side="left", pady=8)

        self.cursor_label = tk.Label(
            editor_header, text="Ln 1, Col 1",
            bg=PANEL, fg="#999999"
        )
        self.cursor_label.pack(side="right", padx=10)

        code_area = tk.Frame(editor_frame, bg=EDITOR_BG)
        code_area.pack(fill="both", expand=True)

        self.line_numbers = tk.Text(
            code_area, width=4,
            bg="#252526", fg="#858585",
            font=("Consolas", 11),
            relief="flat", state="disabled",
            padx=5, takefocus=0
        )
        self.line_numbers.pack(side="left", fill="y")

        self.editor = tk.Text(
            code_area,
            bg=EDITOR_BG, fg=FG,
            insertbackground="white",
            selectbackground="#264f78",
            font=("Consolas", 11),
            undo=True, wrap="none",
            relief="flat", padx=10, pady=10
        )
        self.editor.pack(side="left", fill="both", expand=True)

        scroll_y = ttk.Scrollbar(
            code_area, orient="vertical",
            command=self.scroll_editor
        )
        scroll_y.pack(side="right", fill="y")

        self.editor.configure(yscrollcommand=scroll_y.set)

        # Right panel
        right = tk.Frame(main, bg=PANEL)
        main.add(right, width=350)

        # Stopwatch
        tk.Label(
            right, text="STOPWATCH",
            bg=PANEL, fg=GREEN,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=12, pady=(12, 3))

        self.stopwatch_label = tk.Label(
            right, text="00:00:00",
            bg=PANEL, fg="white",
            font=("Consolas", 23, "bold")
        )
        self.stopwatch_label.pack(pady=5)

        timer_buttons = tk.Frame(right, bg=PANEL)
        timer_buttons.pack()

        for text, command in [
            ("Start", self.start_stopwatch),
            ("Pause", self.pause_stopwatch),
            ("Reset", self.reset_stopwatch)
        ]:
            tk.Button(
                timer_buttons, text=text,
                command=command,
                bg="#3c3c3c", fg="white",
                relief="flat", padx=8
            ).pack(side="left", padx=3)

        # AI Assistant
        tk.Label(
            right, text="AI PYTHON ASSISTANT",
            bg=PANEL, fg=GREEN,
            font=("Arial", 10, "bold")
        ).pack(anchor="w", padx=12, pady=(25, 5))

        self.ai_question = tk.Text(
            right, height=5,
            bg="#1e1e1e", fg=FG,
            insertbackground="white",
            font=("Arial", 10),
            relief="flat", padx=8, pady=8
        )
        self.ai_question.pack(fill="x", padx=10)

        ai_buttons = [
            ("Ask AI", self.ask_ai),
            ("Explain Code", self.explain_code),
            ("Debug Code", self.debug_code),
            ("Suggest ML Algorithm", self.suggest_algorithm)
        ]

        for text, command in ai_buttons:
            tk.Button(
                right, text=text,
                command=command,
                bg="#333333", fg="white",
                relief="flat",
                anchor="w", padx=10
            ).pack(fill="x", padx=10, pady=3)

        # Output area
        output_frame = tk.Frame(self.root, bg="#181818")
        output_frame.pack(fill="both", expand=False)

        output_header = tk.Frame(output_frame, bg="#333333")
        output_header.pack(fill="x")

        tk.Label(
            output_header, text="  TERMINAL / OUTPUT",
            bg="#333333", fg=GREEN,
            font=("Arial", 9, "bold")
        ).pack(side="left", pady=7)

        self.status_label = tk.Label(
            output_header, text="Ready",
            bg="#333333", fg="#aaaaaa"
        )
        self.status_label.pack(side="right", padx=12)

        self.output = tk.Text(
            output_frame, height=9,
            bg="#181818", fg="#cccccc",
            insertbackground="white",
            font=("Consolas", 10),
            relief="flat", padx=10, pady=8
        )
        self.output.pack(fill="both", expand=True)

        self.write_output(
            "Python Workspace 1.0 started.\n"
            "Press F5 or click Run to execute your code.\n\n"
        )

    # ---------------- EDITOR ----------------

    def insert_welcome_code(self):
        welcome = '''# Welcome to Python Workspace 1.0

print("Hello, World!")

name = "Python Developer"
print("Welcome,", name)

# Try your own Python code below.
'''
        self.editor.insert("1.0", welcome)
        self.highlight_syntax()

    def on_editor_change(self, event=None):
        self.update_line_numbers()
        self.highlight_syntax()
        self.update_cursor_position()

    def update_line_numbers(self):
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", "end")

        last_line = int(self.editor.index("end-1c").split(".")[0])

        numbers = "\n".join(str(i) for i in range(1, last_line + 1))
        self.line_numbers.insert("1.0", numbers)
        self.line_numbers.config(state="disabled")

    def sync_scroll(self, event=None):
        self.line_numbers.yview_moveto(
            self.editor.yview()[0]
        )

    def scroll_editor(self, *args):
        self.editor.yview(*args)
        self.line_numbers.yview(*args)

    def update_cursor_position(self, event=None):
        position = self.editor.index("insert")
        line, column = position.split(".")
        self.cursor_label.config(
            text=f"Ln {line}, Col {int(column) + 1}"
        )

    def highlight_syntax(self):

        code = self.editor.get("1.0", "end-1c")

        for tag in [
            "keyword", "string", "comment",
            "number", "function"
        ]:
            self.editor.tag_remove(tag, "1.0", "end")

        patterns = {
            "keyword": r"\b(def|class|return|if|else|elif|for|while|"
                       r"import|from|as|try|except|finally|with|"
                       r"pass|break|continue|in|is|not|and|or|"
                       r"True|False|None|lambda|yield|async|await)\b",

            "string": r"(['\"].*?['\"])",

            "comment": r"#.*",

            "number": r"\b\d+(\.\d+)?\b",

            "function": r"\b[A-Za-z_]\w*(?=\s*\()"
        }

        colours = {
            "keyword": PURPLE,
            "string": ORANGE,
            "comment": "#6a9955",
            "number": GREEN,
            "function": YELLOW
        }

        for tag, pattern in patterns.items():
            self.editor.tag_configure(
                tag, foreground=colours[tag]
            )

            for match in re.finditer(
                pattern, code, re.MULTILINE
            ):
                start = f"1.0+{match.start()}c"
                end = f"1.0+{match.end()}c"
                self.editor.tag_add(tag, start, end)

    # ---------------- FILE MANAGEMENT ----------------

    def new_file(self):
        self.editor.delete("1.0", "end")
        self.current_file = None
        self.file_label.config(text="  untitled.py")
        self.update_line_numbers()

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[
                ("Python files", "*.py"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                code = file.read()

            self.editor.delete("1.0", "end")
            self.editor.insert("1.0", code)

            self.current_file = path
            self.file_label.config(
                text="  " + os.path.basename(path)
            )
            self.on_editor_change()

        except Exception as error:
            messagebox.showerror("Open Error", str(error))

    def save_file(self):
        if not self.current_file:
            self.current_file = filedialog.asksaveasfilename(
                defaultextension=".py",
                filetypes=[("Python files", "*.py")]
            )

        if not self.current_file:
            return

        try:
            code = self.editor.get("1.0", "end-1c")

            with open(
                self.current_file, "w", encoding="utf-8"
            ) as file:
                file.write(code)

            self.file_label.config(
                text="  " + os.path.basename(self.current_file)
            )
            self.status_label.config(text="Saved")

        except Exception as error:
            messagebox.showerror("Save Error", str(error))

    # ---------------- PYTHON EXECUTION ----------------

    def run_code(self):

        code = self.editor.get("1.0", "end-1c")

        if not code.strip():
            return

        self.clear_output()
        self.write_output("Running Python program...\n\n")
        self.status_label.config(text="Running")

        def execute():

            try:
                with tempfile.NamedTemporaryFile(
                    mode="w",
                    suffix=".py",
                    encoding="utf-8",
                    delete=False
                ) as file:
                    file.write(code)
                    filename = file.name

                result = subprocess.run(
                    [sys.executable, filename],
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.path.dirname(
                        self.current_file
                    ) if self.current_file else None
                )

                output_text = result.stdout
                error_text = result.stderr

                self.root.after(
                    0, lambda: self.show_execution_result(
                        output_text, error_text, result.returncode
                    )
                )

            except subprocess.TimeoutExpired:
                self.root.after(
                    0, lambda: self.show_execution_result(
                        "", "Execution timed out after 30 seconds.", 1
                    )
                )

            except Exception as error:
                self.root.after(
                    0, lambda: self.show_execution_result(
                        "", str(error), 1
                    )
                )

            finally:
                try:
                    os.remove(filename)
                except (OSError, UnboundLocalError):
                    pass

        threading.Thread(
            target=execute, daemon=True
        ).start()

    def show_execution_result(self, stdout, stderr, code):

        if stdout:
            self.write_output(stdout)

        if stderr:
            self.write_output("\nERROR:\n" + stderr)

        if not stdout and not stderr:
            self.write_output("Program finished with no output.\n")

        self.write_output(
            f"\n\nProcess finished with exit code {code}."
        )

        self.status_label.config(
            text="Finished" if code == 0 else "Error"
        )

    def clear_output(self):
        self.output.delete("1.0", "end")

    def write_output(self, text):
        self.output.insert("end", text)
        self.output.see("end")

    # ---------------- CLOCK ----------------

    def update_clock(self):
        current = time.strftime("%A, %d %B %Y  |  %H:%M:%S")
        self.clock_label.config(text=current)
        self.root.after(1000, self.update_clock)

    # ---------------- STOPWATCH ----------------

    def start_stopwatch(self):
        if not self.running:
            self.start_time = time.time()
            self.running = True

    def pause_stopwatch(self):
        if self.running:
            self.elapsed += time.time() - self.start_time
            self.running = False

    def reset_stopwatch(self):
        self.elapsed = 0
        self.start_time = None
        self.running = False
        self.stopwatch_label.config(text="00:00:00")

    def update_stopwatch(self):

        total = self.elapsed

        if self.running:
            total += time.time() - self.start_time

        seconds = int(total)
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        self.stopwatch_label.config(
            text=f"{hours:02}:{minutes:02}:{seconds:02}"
        )

        self.root.after(200, self.update_stopwatch)

    # ---------------- AI ASSISTANT ----------------

    def get_ai_client(self):

        if OpenAI is None:
            messagebox.showerror(
                "Missing package",
                "Install the OpenAI package first:\n\npip install openai"
            )
            return None

        if not os.environ.get("OPENAI_API_KEY"):
            messagebox.showwarning(
                "API key required",
                "Set your OPENAI_API_KEY environment variable first."
            )
            return None

        return OpenAI()

    def get_code(self):
        return self.editor.get("1.0", "end-1c")

    def get_selected_code(self):
        try:
            return self.editor.get("sel.first", "sel.last")
        except tk.TclError:
            return self.get_code()

    def ask_ai(self):
        question = self.ai_question.get("1.0", "end-1c").strip()

        if not question:
            messagebox.showinfo(
                "AI Assistant",
                "Type a question first."
            )
            return

        self.call_ai(
            question + "\n\nRelevant Python code:\n" +
            self.get_selected_code()
        )

    def explain_code(self):
        self.call_ai(
            "Explain this Python code step by step for a beginner:\n\n" +
            self.get_selected_code()
        )

    def debug_code(self):
        self.call_ai(
            "Find bugs in this Python code. Explain the problems "
            "and provide corrected code:\n\n" +
            self.get_selected_code()
        )

    def suggest_algorithm(self):
        self.call_ai(
            "I am learning machine learning. Examine this code or "
            "project idea and suggest suitable machine learning "
            "algorithms, explaining why:\n\n" +
            self.get_selected_code()
        )

    def call_ai(self, prompt):

        client = self.get_ai_client()

        if client is None:
            return

        self.write_output("\n\nAI is thinking...\n")
        self.status_label.config(text="AI working")

        def request():

            try:
                response = client.responses.create(
                    model=MODEL,
                    instructions=(
                        "You are a helpful Python, engineering, "
                        "robotics and machine learning tutor. "
                        "Explain concepts clearly to a beginner. "
                        "When debugging, identify the cause and "
                        "show corrected code."
                    ),
                    input=prompt
                )

                answer = response.output_text

                self.root.after(
                    0, lambda: self.show_ai_answer(answer)
                )

            except Exception as error:
                error_message = str(error)
                self.root.after(
                    0, lambda: self.show_ai_answer(
                        "AI request failed:\n" + error_message
                    )
                )

        threading.Thread(
            target=request, daemon=True
        ).start()

    def show_ai_answer(self, answer):
        self.write_output("\n\n========== AI ASSISTANT ==========\n")
        self.write_output(answer)
        self.write_output("\n\n==================================\n")
        self.status_label.config(text="Ready")


# ---------------- START APPLICATION ----------------

if __name__ == "__main__":
    root = tk.Tk()
    app = PythonWorkspace(root)
    root.mainloop()
