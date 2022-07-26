import configparser
import time
import traceback
import codecs
import psutil
import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

media_app_name = None  # for killing and starting
media_app_dir = None  # for starting the media player
media_path = None  # for monitoring changes
file_types = []  # for monitoring changes


def run_all_files():
    files_list = [os.path.join(media_path, x) for x in os.listdir(media_path) if
                  any([x.lower().endswith(ft) for ft in file_types])]
    print("files to run {}".format(len(files_list)))
    # run cmd os.path.join(media_app_dir, media_process_name) with all files under dir
    files_list.insert(0, os.path.join(media_app_dir, media_app_name))
    subprocess.Popen(files_list)
    print("started media player")


def get_process_cmd(proc):
    cmd = ""
    try:
        cmd = proc.cmdline()
    except psutil.AccessDenied:
        pass
    return cmd


def get_running_process(process_name):
    active_processes = []

    processes = psutil.process_iter()
    for process in processes:
        try:
            # print(f'Process: {process}')
            # print(f'id: {process.pid}')
            # print(f'name: {process.name()}')
            # print(f'cmdline: {process.cmdline()}')
            if process_name == process.name() or process_name in get_process_cmd(process):
                active_processes.append(process)
        except Exception as start_process_exception:
            print(f"{traceback.format_exc()}")

    return active_processes


def is_media_player_running():
    active_processes = get_running_process(media_app_name)
    return len(active_processes) > 0


def kill(process_name):
    """Kill Running Process by using it's name
    - Generate list of processes currently running
    - Iterate through each process
        - Check if process name or cmdline matches the input process_name
        - Kill if match is found
    Parameters
    ----------
    process_name: str
        Name of the process to kill (ex: HD-Player.exe)
    Returns
    -------
    None
    """
    try:
        print(f'Killing processes {process_name}')
        active_processes = get_running_process(process_name)
        if len(active_processes) > 0:
            print(f'Found {len(active_processes)} {process_name} running')
            for process in active_processes:
                process.terminate()
                print(f'killed')

    except Exception:
        print(f"{traceback.format_exc()}")


def on_created(event):
    print(f"hey, {event.src_path} has been created!")


def on_deleted(event):
    print(f"what the f**k! Someone deleted {event.src_path}!")


def on_modified(event):
    print(f"hey buddy, {event.src_path} has been modified")


def on_moved(event):
    print(f"ok ok ok, someone moved {event.src_path} to {event.dest_path}")


def on_changed(event):
    print("files changed")
    kill(media_app_name)
    run_all_files()


def get_config(section, option, default=None):
    return config.get(section, option) if config.has_option(section, option) else default


if __name__ == "__main__":
    try:
        config = configparser.ConfigParser()
        config_path = next((x for x in os.listdir(os.getcwd()) if x.lower().endswith(".ini")), os.getcwd())
        if os.path.exists(config_path) and os.path.isfile(config_path):
            config.read_file(codecs.open(config_path, encoding='utf-8'))

        media_path = get_config("global", "path", "C:\\Users\\טלויזיה\\Desktop\\סרטונים")
        file_types = [x.strip() for x in get_config("global", "file_types", ".mp4").split(",")]
        media_app_dir = get_config("global", "media_app_dir", "C:\\Program Files (x86)\\Windows Media Player\\")
        media_app_name = get_config("global", "media_app_name", "wmplayer.exe")

        patterns = ["*"]
        ignore_patterns = None
        ignore_directories = False
        case_sensitive = True
        my_event_handler = PatternMatchingEventHandler(patterns, ignore_patterns, ignore_directories, case_sensitive)
        my_event_handler.on_created = on_changed  # on_created
        my_event_handler.on_deleted = on_changed  # on_deleted
        # my_event_handler.on_modified = on_changed  # on_modified
        my_event_handler.on_moved = on_changed  # on_moved

        if not is_media_player_running():
            run_all_files()

        go_recursively = True
        my_observer = Observer()
        my_observer.schedule(my_event_handler, media_path, recursive=go_recursively)
        my_observer.start()
        print("Monitoring '{}'".format(media_path))
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            my_observer.stop()
            my_observer.join()
    except Exception as e:
        print(f"{traceback.format_exc()}")
        input("Press any key to exit")
