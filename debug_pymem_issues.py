import ctypes
import sys
import pymem
import pymem.process
import psutil


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def get_gta5_pid(process_name="GTA5.exe"):
    for proc in psutil.process_iter(["pid", "name"]):
        if proc.info["name"] == process_name:
            return proc.info["pid"]
    return None


class GameMemory:
    def __init__(self, pm):
        self.pm = pm

    def pattern_scan(self, pattern, mask):
        module = pymem.process.module_from_name(self.pm.process_handle, "GTA5.exe")
        module_base = module.lpBaseOfDll
        module_size = module.SizeOfImage

        bytes_array = self.pm.read_bytes(module_base, module_size)

        pattern_bytes = bytes.fromhex(pattern.replace(" ", ""))
        mask_pattern = "".join(["." if x == "?" else "\\x%02x" % ord(x) for x in mask])

        for i in range(len(bytes_array) - len(pattern_bytes)):
            match = True
            for j in range(len(pattern_bytes)):
                if mask_pattern[j] != "." and pattern_bytes[j] != bytes_array[i + j]:
                    match = False
                    break
            if match:
                return module_base + i
        return None


def main():
    process_name = "GTA5.exe"
    pid = get_gta5_pid(process_name)

    if pid is None:
        print(f"{process_name} not found.")
        return

    print(f"Found {process_name} with PID {pid}")

    try:
        pm = pymem.Pymem(pid)
        print(f"Attempting to open process with PID {pid}")

        if pm.process_handle:
            print(f"Successfully opened process {process_name} with PID {pid}")

            # Pattern and mask for game state (example)
            GAME_STATE_PATTERN = "83 3D ?? ?? ?? ?? ?? 75 17 8B 43 20 25"
            GAME_STATE_MASK = "xx?????xxxxx"

            game_memory = GameMemory(pm)
            address = game_memory.pattern_scan(GAME_STATE_PATTERN, GAME_STATE_MASK)

            if address:
                print(f"Pattern found at address: {hex(address)}")

                # Trying different data types
                try:
                    value = pm.read_longlong(address + 2)
                    print(f"Read long long value: {value}")
                except Exception as e:
                    print(f"Error reading long long: {e}")

                try:
                    value = pm.read_int(address + 2)
                    print(f"Read int value: {value}")
                except Exception as e:
                    print(f"Error reading int: {e}")

                try:
                    value = pm.read_float(address + 2)
                    print(f"Read float value: {value}")
                except Exception as e:
                    print(f"Error reading float: {e}")
            else:
                print("Pattern not found.")
        else:
            print(f"Failed to open process {process_name} with PID {pid}")

    except pymem.exception.ProcessNotFound as e:
        print(f"Could not open process with PID {pid}. Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
