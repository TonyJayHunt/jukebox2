import tkinter as tk
from utils import center_window  # Import center_window
def confirm_dialog(parent, message):
    """Custom Yes/No confirmation dialog."""
    response = [False]
    dialog = tk.Toplevel(parent)
    dialog.title("Confirm")
    dialog.geometry("400x200")
    tk.Label(dialog, text=message, font=('Helvetica', 16),
             wraplength=350, justify='center').pack(pady=20)
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)

    yes_btn = tk.Button(btn_frame, text="Yes",
                        command=lambda: _set_response_and_destroy(dialog,
                                                                response, True),
                        width=12, height=2, font=('Helvetica', 14))
    yes_btn.pack(side='left', padx=20, pady=10)

    no_btn = tk.Button(btn_frame, text="No",
                       command=lambda: _set_response_and_destroy(dialog,
                                                               response, False),
                       width=12, height=2, font=('Helvetica', 14))
    no_btn.pack(side='left', padx=20, pady=10)

    dialog.transient(parent)
    dialog.grab_set()
    center_window(dialog)
    parent.wait_window(dialog)
    return response[0]

def confirm_dialog_error(parent, message):
    """Custom Yes/No confirmation dialog."""
    response = [False]
    dialog = tk.Toplevel(parent)
    dialog.title("Confirm")
    dialog.geometry("400x200")
    tk.Label(dialog, text=message, font=('Helvetica', 16),
             wraplength=350, justify='center').pack(pady=20)
    btn_frame = tk.Frame(dialog)
    btn_frame.pack(pady=10)

    no_btn = tk.Button(btn_frame, text="OK",
                       command=lambda: _set_response_and_destroy(dialog,
                                                               response, False),
                       width=12, height=2, font=('Helvetica', 14))
    no_btn.pack(side='left', padx=20, pady=10)

    dialog.transient(parent)
    dialog.grab_set()
    center_window(dialog)
    parent.wait_window(dialog)
    return response[0]

def _set_response_and_destroy(dialog, response, value):
    response[0] = value
    dialog.destroy()


def password_dialog(parent, prompt):
    """Custom password input dialog (placeholder for keyboard)."""

    response = [None]
    dialog = tk.Toplevel(parent)
    dialog.title("Password Required")
    dialog.geometry("400x200")
    tk.Label(dialog, text=prompt, font=('Helvetica', 16),
             wraplength=350, justify='center').pack(pady=10)
    entry_var = tk.StringVar()
    entry = tk.Entry(dialog, textvariable=entry_var, show='*',
                     font=('Helvetica', 16))
    entry.pack(pady=10)

    ok_btn = tk.Button(dialog, text="OK",
                        command=lambda: _get_password_and_destroy(dialog,
                                                                response,
                                                                entry_var.get()),
                        width=12, height=2, font=('Helvetica', 14))
    ok_btn.pack(pady=20)

    # Placeholder for on-screen keyboard integration
    # ... (Keyboard code or external widget here)

    dialog.transient(parent)
    dialog.grab_set()
    center_window(dialog)
    parent.wait_window(dialog)
    return response[0]


def _get_password_and_destroy(dialog, response, password):
    response[0] = password
    dialog.destroy()