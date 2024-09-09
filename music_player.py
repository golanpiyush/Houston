import os
import platform
import subprocess
import yt_dlp as ydl
import logging
import atexit
import signal
import threading
import time
import sys

# Disable yt_dlp logging
logging.getLogger('yt_dlp').setLevel(logging.WARNING)

# Add color codes for better CLI visualization
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Function to print colored messages
def print_colored(message, color):
    print(f"{color}{message}{Colors.ENDC}")

class MusicPlayer:
    def __init__(self):
        self.current_process = None
        self.stop_event = threading.Event()  # Event to signal termination
        self.loop_thread = None  # Thread for looping music
        self.is_playing = False  # Track if music is currently playing
        self.is_paused = False  # Track if music is currently paused
        self.loop = False  # Track if looping is enabled
        self.loop_info = None  # Store information for looping
        self._set_socket_path()
        atexit.register(self.cleanup)  # Register cleanup function to be called on exit
        signal.signal(signal.SIGINT, self.signal_handler)  # Handle SIGINT
        signal.signal(signal.SIGTERM, self.signal_handler)  # Handle SIGTERM

    def _set_socket_path(self):
        if platform.system() == 'Windows':
            self.socket_path = r'\\.\pipe\mpvsocket'
        else:
            self.socket_path = '/tmp/mpvsocket'

    #downloader


    def downloader(self):
        if not hasattr(self, 'current_url') or not self.current_url:
            print_colored("No song is currently playing to download.", Colors.FAIL)
            return
        
        # Create 'Houston Songs' directory if it doesn't exist
        download_dir = os.path.join(os.getcwd(), 'Houston Songs')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        try:
            # Define progress hook to show download progress
            def progress_hook(d):
                if d['status'] == 'downloading':
                    total_bytes = d.get('total_bytes', 0)
                    downloaded_bytes = d.get('downloaded_bytes', 0)
                    if total_bytes:
                        progress = downloaded_bytes / total_bytes * 100
                        sys.stdout.write(f"\rDownloading: {progress:.2f}% complete")
                        sys.stdout.flush()
                elif d['status'] == 'finished':
                    print_colored("\nDownload finished.", Colors.OKCYAN)
            
            # Specify yt-dlp download options
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),  # Save with original title and extension
                'quiet': True,  # Suppress yt-dlp output
                'noplaylist': True,  # Only download the single song
                'progress_hooks': [progress_hook],  # Hook to track download progress
            }

            # Use yt-dlp to download the song
            with ydl.YoutubeDL(ydl_opts) as ydl_instance:
                print_colored(f"Downloading song: {self.current_url}", Colors.OKCYAN)
                info_dict = ydl_instance.extract_info(self.current_url, download=True)

                # Construct file paths
                original_file = os.path.join(download_dir, f"{info_dict['title']}.{info_dict['ext']}")
                mp3_file = os.path.join(download_dir, f"{info_dict['title']}.mp3")

                # Rename the downloaded file to .mp3 and handle potential existing file conflicts
                if os.path.exists(original_file):
                    if os.path.exists(mp3_file):
                        print_colored(f"File {mp3_file} already exists. Renaming with a unique identifier.", Colors.WARNING)
                        base, ext = os.path.splitext(mp3_file)
                        i = 1
                        while os.path.exists(f"{base}_{i}{ext}"):
                            i += 1
                        mp3_file = f"{base}_{i}{ext}"

                    # Rename the file to .mp3
                    os.rename(original_file, mp3_file)
                    print_colored(f"Download completed and saved as '{mp3_file}'.", Colors.OKGREEN)
                else:
                    print_colored("Downloaded file not found.", Colors.FAIL)

        except Exception as e:
            print_colored(f"Download failed: {e}", Colors.FAIL)



    def play_music(self, url):
        self.current_url = url  # Set current_url attribute
        self.stop_music()  # Stop currently playing music
        self._set_socket_path()  # Reset socket path each time

        system_platform = platform.system()
        mpv_path = ''

        if system_platform == 'Windows':
            mpv_path = os.path.join(os.path.dirname(__file__), 'third_party', 'mpv', 'mpv.exe')
        elif system_platform in ('Darwin', 'Linux'):  # For macOS and Linux
            mpv_path = 'mpv'
        else:
            print_colored("Unsupported platform.", Colors.FAIL)
            return 

        cmd = [mpv_path, '--no-video', f'--input-ipc-server={self.socket_path}', url]

        self.current_process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.is_playing = True  # Set playing state to True
        self.is_paused = False  # Reset paused state
        print_colored("Playing music.", Colors.OKGREEN)

    def stop_music(self):
        if self.current_process:
            self._send_command('quit')
            try:
                self.current_process.wait(timeout=5)  # Wait for process to terminate
                print_colored("mpv process terminated gracefully", Colors.OKGREEN)
            except subprocess.TimeoutExpired:
                self.current_process.kill()  # Force kill if it doesn't terminate
                print_colored("mpv process killed forcefully", Colors.WARNING)
            self.current_process = None
            self.is_playing = False  # Set playing state to False
            self.is_paused = False  # Reset paused state

    def pause_music(self):
        if self.current_process and self.is_playing and not self.is_paused:
            self._send_command('cycle pause')
            print_colored("Music paused.", Colors.OKBLUE)
            self.is_paused = True  # Set paused state to True
        elif self.is_paused:
            print_colored("Music is already paused.", Colors.WARNING)
        else:
            print_colored("No song is currently playing.", Colors.FAIL)

    def resume_music(self):
        if self.current_process and self.is_playing and self.is_paused:
            self._send_command('cycle pause')
            print_colored("Music resumed.", Colors.OKBLUE)
            self.is_paused = False  # Reset paused state
        elif self.is_playing and not self.is_paused:
            print_colored("Music is already playing.", Colors.WARNING)
        else:
            print_colored("No song is currently paused or song is already playing.", Colors.FAIL)

    def _send_command(self, command):
        if self.current_process:
            try:
                with open(self.socket_path, 'w') as f:
                    f.write(command + '\n')
            except Exception as e:
                print_colored(f"Error sending command to mpv: {e}", Colors.FAIL)

    def cleanup(self):
        self.stop_music()
        print_colored("Cleanup completed", Colors.OKCYAN)

    def signal_handler(self, sig, frame):
        self.cleanup()
        os._exit(0)  # Force exit the program

    def _loop_music(self):
        while not self.stop_event.is_set():
            if self.loop and self.loop_info and self.is_playing:
                time.sleep(1)  # Check every second if music needs to be looped
                if self.current_process and self.current_process.poll() is not None:  # Check if process has terminated
                    audio_url, title = self.loop_info
                    print_colored(f"Replaying: {title}", Colors.OKCYAN)
                    self.play_music(audio_url)  # Restart music with the stored song information
            else:
                self.stop_event.wait(1)  # Wait before checking again

    def get_audio_info(self, song_name):
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,  # Disable yt_dlp console output
        }
        with ydl.YoutubeDL(ydl_opts) as ydl_instance:
            try:
                search_results = ydl_instance.extract_info(f"ytsearch:{song_name}", download=False)
                if search_results and 'entries' in search_results:
                    first_result = search_results['entries'][0]
                    return first_result['url'], first_result['title']
                else:
                    print_colored("No results found for the provided song name.", Colors.WARNING)
                    return None, None
            except Exception as e:
                print_colored(f"Error: {e}", Colors.FAIL)
                return None, None
