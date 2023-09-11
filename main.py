"""
1 - Add user via Gpedit.msc
2 - install service: python my_service.py install
3 - start service: python my_service.py start

Official documentation of how to install the service: use sc (Service Control)

    1. Create a `.bat` file that runs your Python script.
    2. Open a command prompt as an administrator.
    3. Use the `sc` command to create a new service that will execute the `.bat` file.

   ```cmd
   sc create YourServiceName binPath= "C:\Path\To\Your\Batch\File.bat" start= auto
   ```

Windows Constraints
1. Administrative Rights: To kill processes, the service must be run with
   administrative privileges.
2. Absolute Paths: Make sure to use absolute paths in your script and service file,
   as the working directory may differ when running as a service.
3. Dependencies: All Python dependencies must be accessible for the user under which
   the service is run.
4. User Interactions: Windows services run in the background and cannot directly
   interact with the user interface. If your code requires user interaction, you will
   need to find another way to manage it.
5. Logs and Debugging: Debugging can be more complicated when a program is run as a
   service. Adding a logging system to your script may be helpful.
6. Error Handling: Windows services can be configured to automatically restart in case
   of an error, but it's still good to handle errors in your script to avoid
   unexpected behaviors.

SMWinservice
Base class to create winservice in Python
-----------------------------------------
Instructions:
1. Just create a new class that inherits from this base class
2. Define into the new class the variables
   _svc_name_ = "nameOfWinservice"
   _svc_display_name_ = "name of the Winservice that will be displayed in scm"
   _svc_description_ = "description of the Winservice that will be displayed in scm"
3. Override the three main methods:
    def start(self) : if you need to do something at the service initialization.
                      A good idea is to put here the initialization of the running
                      condition
    def stop(self)  : if you need to do something just before the service is stopped.
                      A good idea is to put here the invalidation of the running
                      condition
    def main(self)  : your actual run loop. Just create a loop based on your running
                      condition
4. Define the entry point of your module calling the method "parse_command_line" of
   the new class
5. Enjoy
Credits: Davide Mastromatteo
"""
import datetime
import logging
import socket
from typing import Any, Optional

import psutil
import servicemanager
import win32event
import win32service
import win32serviceutil


class SMWinservice(win32serviceutil.ServiceFramework):
    """Base class for Windows service in Python."""

    _svc_name_: str = "pythonService"
    _svc_display_name_: str = "Python Service"
    _svc_description_: str = "Python Service Description"

    @classmethod
    def parse_command_line(cls) -> None:
        """Handle Windows service setup through command line."""
        win32serviceutil.HandleCommandLine(cls)

    def __init__(self, args: Any) -> None:
        super().__init__(args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        socket.setdefaulttimeout(60)

    def SvcStop(self) -> None:
        """Terminate the service."""
        self.stop()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self) -> None:
        """Execute when the service starts."""
        try:
            self.start()
            servicemanager.LogMsg(
                servicemanager.EVENTLOG_INFORMATION_TYPE,
                servicemanager.PYS_SERVICE_STARTED,
                (self._svc_name_, ""),
            )
            self.main()
        except Exception as e:
            logging.error(f"Exception during start: {e}")

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def main(self) -> None:
        pass


FORMATMSG = "[%(asctime)-20s] %(levelname)-8.8s %(message)s"
FORMAT_TIME_STAMP = "%Y-%m-%d %H:%M:%S"

logging.basicConfig(
    filename=r"D:\pythonprojects\hqf_windows_service\hqf_service.log",
    level=logging.INFO,
    format=FORMATMSG,
    datefmt=FORMAT_TIME_STAMP,
)


class MonService(SMWinservice):
    _svc_name_ = "HQFServerService"
    _svc_display_name_ = "HQF Server Service"
    _svc_description_ = "HQF Server Service to manage a PC"

    @staticmethod
    def get_running_processes():
        processes = {}
        for process in psutil.process_iter():
            try:
                pid = process.pid
                name = process.name()
                processes[pid] = name
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        return processes

    def log_changes(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        old_pids = set(self.old_processes.keys())
        new_processes = self.get_running_processes()
        new_pids = set(new_processes.keys())
        started_pids = new_pids - old_pids
        ended_pids = old_pids - new_pids

        for pid in started_pids:
            logging.info(f"{timestamp} - Process started: {new_processes[pid]}")

        for pid in ended_pids:
            logging.info(f"{timestamp} - Process ended: {self.old_processes[pid]}")
        return new_processes

    def __init__(self, args):
        super().__init__(args)
        self.PORT = 65432
        self.HOST = "127.0.0.1"
        self.old_processes = self.get_running_processes()
        self.is_running = False

    def start(self):
        logging.info("Service start")
        self.is_running = True

    def stop(self):
        logging.info("Service stop")
        self.is_running = False

    @staticmethod
    def kill_process(target_name):
        for process in psutil.process_iter():
            try:
                pid = process.pid
                name = process.name()
                # logging.info(f"Listed process: {name=}..")
                if name == target_name:
                    logging.info(f"Found! Killing!")
                    psutil.Process(pid).terminate()
                    break
            except psutil.ZombieProcess:
                logging.info("ZombieProcess: Process is already terminated.")
            except psutil.NoSuchProcess:
                logging.info("NoSuchProcess: Process does not exist.")
            except psutil.AccessDenied:
                logging.info("AccessDenied: Insufficient permissions.")

    @staticmethod
    def receive_all(conn: socket, buffer_size: int = 1024) -> Optional[bytes]:
        chunks = bytearray()
        while True:
            chunk = conn.recv(buffer_size)
            if not chunk:
                break
            chunks.extend(chunk)
        return chunks if chunks else None

    def handle_client_connection(self, conn):
        log_path = logging.getLogger().handlers[0].baseFilename
        filtered_logs = []
        try:
            with open(log_path, "r") as f:
                for line in f:
                    if "Process" in line:
                        filtered_logs.append(line)
        except FileNotFoundError:
            logging.info(f"Log file {log_path} not found.")
            filtered_logs = ["Log file not found."]

        conn.sendall("".join(filtered_logs).encode("utf-8"))
        received_data_bytes = self.receive_all(conn)
        if received_data_bytes:
            received_data = received_data_bytes.decode("utf-8")
            logging.info(f"Try to kill process {received_data=}.")
            self.kill_process(received_data)
        else:
            logging.info("Client sent an empty message.")

        conn.close()

    def main(self):
        logging.info("Main...")

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.HOST, self.PORT))
            s.listen()
            s.settimeout(2)

            while self.is_running:
                self.old_processes = self.log_changes()
                try:
                    conn, addr = s.accept()
                except socket.timeout:
                    logging.info("No client connected in the last 2 seconds.")
                    continue
                try:
                    self.handle_client_connection(conn)
                except ConnectionResetError:
                    logging.info(
                        "Une connexion existante a été fermée par l'hôte distant."
                    )

                logging.info("Loop...")

    @classmethod
    def parse_command_line(cls):
        logging.info("parse_command_line...")
        super().parse_command_line()


if __name__ == "__main__":
    logging.info("__main__")
    MonService.parse_command_line()
    logging.info("__main__")
