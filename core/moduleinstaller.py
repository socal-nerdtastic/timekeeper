#!/usr/bin/env python3

# see https://github.com/socal-nerdtastic/moduleinstaller for definitive version

"""
packages are in the format {importname:installname}.
These are often the same name, but sometimes not.

HOW TO USE for command-line programs:
Save this python file into your project folder. Then add this code to your main program:

    import moduleinstaller
    moduleinstaller.cli_check_and_prompt({"PIL":"pillow", "pyopenxl":"pyopenxl"})

---

HOW TO USE for GUI programs:
Save this python file into your project folder. Then add this code to your main program:

    import moduleinstaller
    moduleinstaller.gui_check_and_prompt({"PIL":"pillow", "pyopenxl":"pyopenxl"})

This is required for GUI programs that don't have a CLI at all
But is also allowed for CLI programs that want a GUI prompt.

---

ALTERNATE USE:
pass in a string of modules to be installed, or leave
  blank to use requirements.txt file from the same folder.
This alternate method is MUCH SLOWER than the dictionary method.

    import moduleinstaller
    moduleinstaller.cli_check_and_prompt("pillow openpyxl")

or

    import moduleinstaller
    moduleinstaller.cli_check_and_prompt() # use requirements.txt

You can get the speed advantage back if you wrap your attempted import

    try:
        from PIL import Image
        import openpyxl
    except ImportError:
        import moduleinstaller
        moduleinstaller.cli_check_and_prompt("pillow openpyxl")

---

The force_kill argument will force a reboot if any modules are missing,
False = allow program to continue, whether or not modules are missing
True = kill the program if any modules are missing, whether or not the user opts to install them (default)
None = kill the program only if the user declines to install missing modules

---

Normal pip versioning strings can be used. For example

    import moduleinstaller
    moduleinstaller.cli_check_and_prompt({"serial":"pyserial", "openpyxl":"openpyxl==2.2"})

or

    import moduleinstaller
    moduleinstaller.cli_check_and_prompt("pyserial pillow openpyxl==2.2")

"""

class ModuleInstallerCore:
    __version__ = 2024,5,8

    def find_missing(self, install:str|dict=None):
        if isinstance(install, dict):
            return self.find_missing_via_imports(install)
        else: # string, None, or Path
            return self.find_missing_via_pip(install)

    def find_missing_via_pip(self, install:str=None) -> dict:
        import subprocess
        import sys
        from pathlib import Path
        to_be_installed = []
        if install is None:
            req = Path(__file__).parent / "requirements.txt"
            if req.exists():
                install = req.read_text()
            else:
                raise FileNotFoundError(f"No module list supplied and no requirements.txt found at {req}")
        resp = subprocess.run([sys.executable, '-m', 'pip', 'freeze'], capture_output=True)
        installed = resp.stdout.decode().splitlines()
        for modulename in install.strip().split():
            if not any(line.startswith(modulename) for line in installed):
                to_be_installed.append(modulename)
        return to_be_installed

    def find_missing_via_imports(self, install:dict) -> dict:
        # install is a dict of  {importname:installname}
        to_be_installed = []
        for importname, installname in install.items():
            try:
                __import__(importname)
            except (ImportError, ModuleNotFoundError):
                to_be_installed.append(installname)
        return to_be_installed

class ModuleInstallerGUI(ModuleInstallerCore):
    def __init__(self, install:str|dict=None, force_kill:bool=True) -> None:
        if (modules := self.find_missing(install)): # if modules are missing
            if self.show_gui(modules): # and if the user agrees
                self.install_gui(modules) # install missing modules from pip
            if force_kill:
                raise SystemExit

    def show_gui(self, modules:list):
        from tkinter import messagebox
        return messagebox.askyesno(
            "Missing modules", # window title
            f"The following modules are missing:\n\n"
            f"{modules}\n\nWould you like to install them now?")

    def install_gui(self, modules:list):
        from subprocess import Popen, PIPE
        import sys
        import threading
        import tkinter as tk
        from tkinter import ttk
        from tkinter.scrolledtext import ScrolledText

        def pipe_reader(pipe, term=False):
            for line in iter(pipe.readline, b''):
                st.insert(tk.END, line)
                st.see(tk.END)
            if term:
                tk.Label(root, fg='red', text="DONE. Restart required.", font=('bold',14)).pack()
                ttk.Button(root, text="Exit program", command=sys.exit).pack()
        def on_closing(*args):
            print(args)
            root.destroy()
            root.quit()
            sys.exit()

        root = tk.Tk()
        root.protocol("WM_DELETE_WINDOW", on_closing)
        tk.Label(root, text=f'Installing: {", ".join(modules)}', font=('bold',14)).pack()
        st= ScrolledText(root, width=60, height=12)
        st.pack(expand=True, fill=tk.BOTH)
        sub_proc = Popen([sys.executable, '-m', 'pip', 'install'] + modules, stdout=PIPE, stderr=PIPE)
        threading.Thread(target=pipe_reader, args=[sub_proc.stdout]).start()
        threading.Thread(target=pipe_reader, args=[sub_proc.stderr, True]).start()
        root.mainloop()

class ModuleInstallerCLI(ModuleInstallerCore):
    def __init__(self, install:str|dict=None, force_kill:bool=True) -> None:
        if (modules := self.find_missing(install)): # if modules are missing
            if self.show_cli(modules): # and if the user agrees
                self.install_cli(modules) # install missing modules from pip
            if force_kill:
                raise SystemExit

    def show_cli(self, modules:list):
        print("MISSING MODULES")
        print("The following modules are missing:\n")
        print(modules)
        print("\nWould you like to install them now? [no]/yes")
        return input().lower().startswith('y')

    def install_cli(self, modules:list):
        import subprocess
        import sys

        subprocess.run([sys.executable, '-m', 'pip', 'install'] + modules)
        print()
        print("DONE. Restart required.")
        input("press enter to complete")
        sys.exit()

def cli_check_and_prompt(install:str|dict=None, force_kill:bool=True) -> None:
    """
    checks if the given modules are installed or not
    prompts the user to install them if they are not
    """
    ModuleInstallerCLI(install, force_kill)

def gui_check_and_prompt(install:str|dict=None, force_kill:bool=True) -> None:
    """
    checks if the given modules are installed or not
    shows GUI prompt to install them if they are not
    """
    ModuleInstallerGUI(install, force_kill)

def test():
    ModuleInstallerGUI({"pandas":"pillow"})
    # ~ ModuleInstallerCLI({"pandas":"pillow"})
    # ~ gui_check_and_prompt({"serial":"pyserial"})
    # ~ print(find_missing_via_pip("pyserial pillow openpyxl==2.2"))

if __name__ == "__main__":
    test()
    pass
