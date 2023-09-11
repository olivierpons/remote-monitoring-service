import argparse
import multiprocessing
import socket
import os


def out(message: str, process_num: int, total_processes: int):
    """
    Function to display the message with process information.

    Args:
        message (str): The message to display.
        process_num (int): The number of the current process.
        total_processes (int): The total number of processes.
    """
    lines = message.split("\n")
    prefix = f"Process {process_num}/{total_processes}, PID: {os.getpid()} > "
    print(f"{prefix}{lines[0]}")

    for line in lines[1:]:
        print(f"{' ' * len(prefix)}{line}")


def run_client(process_num: int, total_processes: int):
    """
    Function to run the client.

    Args:
        process_num (int): The number of the current process.
        total_processes (int): The total number of processes.
    """
    out("Client process started", process_num, total_processes)

    HOST = "127.0.0.1"
    PORT = 65432

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        data = s.recv(1024)
        out(data.decode(), process_num, total_processes)
        # s.sendall("".encode())
        s.sendall("LeagueClientUxRender.exe".encode())

    out("Client process has terminated", process_num, total_processes)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Launch multiple client processes.")
    parser.add_argument(
        "-n",
        "--num_clients",
        type=int,
        default=1,
        help="Number of client processes to launch",
    )
    args = parser.parse_args()

    processes = []

    for i in range(args.num_clients):
        process = multiprocessing.Process(
            target=run_client, args=(i + 1, args.num_clients)
        )
        processes.append(process)
        process.start()

    for process in processes:
        process.join()
