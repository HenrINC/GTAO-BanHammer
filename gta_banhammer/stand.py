import os
import subprocess
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

import pymem
import psutil


class Stand:
    def __init__(
        self,
        process: psutil.Process,
        pm: pymem.Pymem,
        dll_folder: Path,
        injector_path: Path,
    ) -> None:
        self.module: Optional[pymem.process.Module] = None
        self.injector_path: Path = injector_path
        self.process: psutil.Process = process
        self.dll_folder: Path = dll_folder
        self.pm: pymem.Pymem = pm

    @property
    def is_running(self):
        """
        Checks if the game is running.
        """
        return self.module is not None

    def ensure_dll_up_to_date(self):
        """
        Checks if the DLL is up to date and if not, updates it.
        """
        soup = BeautifulSoup(
            requests.get(
                "https://stand.gg/help/supported-versions",
                # For some reason the powershell UA is not blocked...
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT; Windows NT 10.0; fr-BE) WindowsPowerShell/5.1.22621.2506",
                },
            ).content,
            "html.parser",
        )
        dll = soup.select_one(".content>ul a").get("href").strip("/")
        dll_path = self.dll_folder / dll
        if dll_path.exists():
            os.makedirs(dll_path.parent, exist_ok=True)
            with open(self.dll_folder / dll, "wb") as f:
                f.write(
                    requests.get(
                        f"https://stand.gg/{dll}",
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT; Windows NT 10.0; fr-BE) WindowsPowerShell/5.1.22621.2506",
                        },
                    ).content
                )
        return dll_path

    def attach(self):
        """
        Attaches to the GTA process.
        """
        dll_path = self.ensure_dll_up_to_date()
        module = pymem.process.module_from_name(self.pm.process_handle, dll_path.name)
        if module is None:
            raise RuntimeError("Failed to find the Stand module. Try ijnjecting it.")

    def inject(self):
        """
        Injects the DLL into the GTA process.
        """
        dll_path = self.ensure_dll_up_to_date()
        subprocess.run(
            [
                str(self.injector_path),
                "-p",
                str(self.process.pid),
                "-i",
                str(dll_path),
            ],
            # check=True,
        ).stdout

    def inject_or_attach(self):
        """
        Injects the DLL into the GTA process if it is running, otherwise attaches to it.
        """
        try:
            self.attach()
        except RuntimeError:
            self.inject()

    def ensure_running(self):
        if not self.is_running:
            self.inject_or_attach()
