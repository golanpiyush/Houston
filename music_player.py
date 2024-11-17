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
import re

# Configure logging for yt-dlp
logging.getLogger('yt_dlp').setLevel(logging.WARNING)

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_colored(message, color):
    """Print colored messages to terminal"""
    print(f"{color}{message}{Colors.ENDC}")

class MusicPlayer:
    """
    A music player class that handles YouTube audio playback with effects.
    Supports play, pause, resume, and stop functionality with various audio effects.
    """
    
    def __init__(self):
        """Initialize the music player with necessary attributes and setup"""
        # Core attributes
        self.current_process = None
        self.current_url = None
        self.song_end_event = threading.Event()
        self.monitor_thread = None
        self.stop_event = threading.Event()
        self.loop_thread = None
        
        # State tracking
        self.is_playing = False
        self.is_paused = False
        self.loop = False
        self.loop_info = None
        
        # Effects state
        self.current_effects = set()  # Track active effects
        
        # Setup system-specific configurations
        self._set_socket_path()
        self._setup_mpv_path()
        
        # Initialize signal handlers and cleanup
        self._initialize_signal_handlers()
        atexit.register(self.cleanup)
        
        # Kill any existing mpv processes on startup
        self._kill_existing_mpv()

    def _set_socket_path(self):
        """Set the socket path based on the operating system"""
        self.socket_path = r'\\.\pipe\mpvsocket' if platform.system() == 'Windows' else '/tmp/mpvsocket'

    def _setup_mpv_path(self):
        """Configure the MPV executable path based on the operating system"""
        if platform.system() == 'Windows':
            self.mpv_path = os.path.join(os.path.dirname(__file__), 'third_party', 'mpv', 'mpv.exe')
        else:
            self.mpv_path = 'mpv'

    def _initialize_signal_handlers(self):
        """Initialize signal handlers for graceful shutdown"""
        if threading.current_thread() is threading.main_thread():
            for sig in [signal.SIGINT, signal.SIGTERM]:
                signal.signal(sig, self.signal_handler)

    def _kill_existing_mpv(self):
        """Terminate any existing MPV processes"""
        try:
            if platform.system() == 'Windows':
                subprocess.run(['taskkill', '/F', '/IM', 'mpv.exe'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(['pkill', '-9', 'mpv'], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def _build_audio_effects(self):
        """
        Build the audio effects command string.
        Returns a list of audio filter commands for MPV.
        """
        effects = []
        
        # Base effects (always active)
        effects.extend([
            # Bass boost effect
            '--af=equalizer=f=90:t=q:w=4:g=20',
            'af-add=rubberband=pitch-scale=0.85:tempo-scale=0.8',
            'af-add=ladspa=freeverb:wet=3.0',
            # Basic reverb
            # 'af-add=rubberband=pitch-scale=1.3:tempo-scale=1.2'
        ])
        
        # Optional effects - can be toggled
        if 'nightcore' in self.current_effects:
            # Nightcore effect (increased pitch and speed)
            effects.append('af-add=rubberband=pitch-scale=1.3:tempo-scale=1.2')
        
        if 'vaporwave' in self.current_effects:
            # Vaporwave effect (slowed and reverb)
            effects.append('af-add=rubberband=pitch-scale=0.85:tempo-scale=0.8')
            effects.append('af-add=ladspa=freeverb:wet=3.0')
        
        if 'deep' in self.current_effects:
            # Deep effect (lowered pitch)
            effects.append('af-add=rubberband=pitch-scale=0.7')
        
        if '8bit' in self.current_effects:
            # 8-bit style effect
            effects.append('af-add=lowpass=f=4000,highpass=f=300')
        
        return effects

    def play_music(self, url):
        """
        Play music from the given URL with applied effects
        
        Args:
            url (str): YouTube URL or audio stream URL
        """
        # Stop any existing playback
        self.stop_music()
        time.sleep(0.5)  # Wait for cleanup
        
        # Kill any stray processes and clean up socket
        self._kill_existing_mpv()
        if platform.system() != 'Windows' and os.path.exists(self.socket_path):
            try:
                os.remove(self.socket_path)
            except Exception:
                pass

        # Store current URL
        self.current_url = url
        
        # Build command with effects
        cmd = [self.mpv_path, '--no-video', f'--input-ipc-server={self.socket_path}', url]
        cmd.extend(self._build_audio_effects())

        try:
            self.current_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            self.is_playing = True
            self.is_paused = False
            print_colored("Now playing...", Colors.OKGREEN)
        except Exception as e:
            print_colored(f"Error starting playback: {e}", Colors.FAIL)
            self.is_playing = False
            self.is_paused = False

    def stop_music(self):
        """Stop the current playback and cleanup"""
        if self.current_process:
            try:
                self._send_command('quit')
                try:
                    self.current_process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    self.current_process.kill()
                    self.current_process.wait()
            except Exception:
                try:
                    self.current_process.kill()
                except Exception:
                    pass
            finally:
                self.current_process = None
                self.is_playing = False
                self.is_paused = False
                if platform.system() != 'Windows' and os.path.exists(self.socket_path):
                    try:
                        os.remove(self.socket_path)
                    except Exception:
                        pass

    def downloader(self):
        """Download the currently playing song"""
        if not hasattr(self, 'current_url') or not self.current_url:
            print_colored("No song is currently playing to download.", Colors.FAIL)
            return
        
        download_dir = os.path.join(os.getcwd(), 'Houston Songs')
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        
        try:
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
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(download_dir, '%(title)s.%(ext)s'),
                'quiet': True,
                'noplaylist': True,
                'progress_hooks': [progress_hook],
            }

            with ydl.YoutubeDL(ydl_opts) as ydl_instance:
                print_colored(f"Downloading song: {self.current_url}", Colors.OKCYAN)
                info_dict = ydl_instance.extract_info(self.current_url, download=True)

                original_file = os.path.join(download_dir, f"{info_dict['title']}.{info_dict['ext']}")
                mp3_file = os.path.join(download_dir, f"{info_dict['title']}.mp3")

                if os.path.exists(original_file):
                    if os.path.exists(mp3_file):
                        base, ext = os.path.splitext(mp3_file)
                        i = 1
                        while os.path.exists(f"{base}_{i}{ext}"):
                            i += 1
                        mp3_file = f"{base}_{i}{ext}"

                    os.rename(original_file, mp3_file)
                    print_colored(f"Download completed and saved as '{mp3_file}'.", Colors.OKGREEN)
                else:
                    print_colored("Downloaded file not found.", Colors.FAIL)

        except Exception as e:
            print_colored(f"Download failed: {e}", Colors.FAIL)

    def pause_music(self):
        """Pause the current playback"""
        if self.current_process and self.is_playing and not self.is_paused:
            self._send_command('cycle pause')
            print_colored("Music paused.", Colors.OKBLUE)
            self.is_paused = True
        elif self.is_paused:
            print_colored("Music is already paused.", Colors.WARNING)
        else:
            print_colored("No song is currently playing.", Colors.FAIL)

    def resume_music(self):
        """Resume the paused playback"""
        if self.current_process and self.is_playing and self.is_paused:
            self._send_command('cycle pause')
            print_colored("Music resumed.", Colors.OKBLUE)
            self.is_paused = False
        elif self.is_playing and not self.is_paused:
            print_colored("Music is already playing.", Colors.WARNING)
        else:
            print_colored("No song is currently playing.", Colors.FAIL)

    def _send_command(self, command):
        """Send a command to the MPV process"""
        if self.current_process:
            try:
                with open(self.socket_path, 'w') as f:
                    f.write(command + '\n')
            except Exception as e:
                print_colored(f"Error sending command to mpv: {e}", Colors.FAIL)

    def cleanup(self):
        """Perform cleanup operations before shutdown"""
        print_colored("\nCleaning up...", Colors.OKCYAN)
        self.stop_music()
        self._kill_existing_mpv()
        print_colored("Cleanup completed", Colors.OKGREEN)

    def signal_handler(self, sig, frame):
        """Handle system signals for graceful shutdown"""
        print_colored("\nReceived shutdown signal. Cleaning up...", Colors.WARNING)
        self.cleanup()
        sys.exit(0)

    def get_audio_info(self, song_name_or_url):
  
        youtube_link_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'

        ydl_opts = {
                'format': 'bestaudio/best',
                'quiet': True,
            }
            
        with ydl.YoutubeDL(ydl_opts) as ydl_instance:
                try:
                    if re.match(youtube_link_regex, song_name_or_url):
                        # If the URL is directly given
                        info = ydl_instance.extract_info(song_name_or_url, download=False)
                        return info['url'], info['title']
                    else:
                        # Search and get the first result directly
                        search_results = ydl_instance.extract_info(f"ytsearch:{song_name_or_url} audio", download=False)
                        if search_results and 'entries' in search_results:
                            first_result = search_results['entries'][0]
                            return first_result['url'], first_result['title']
                        else:
                            print_colored("No results found for the provided song name.", Colors.WARNING)
                            return None, None
                except Exception as e:
                    print_colored(f"Error: {e}", Colors.FAIL)
                    return None, None


    

    

    

    def toggle_effect(self, effect_name):
        """
        Toggle an audio effect on/off
        
        Args:
            effect_name (str): Name of the effect to toggle
        """
        if effect_name in self.current_effects:
            self.current_effects.remove(effect_name)
            print_colored(f"{effect_name} effect disabled.", Colors.OKBLUE)
        else:
            self.current_effects.add(effect_name)
            print_colored(f"{effect_name} effect enabled.", Colors.OKGREEN)
            
        # Restart playback with new effects if something is playing
        if self.is_playing and self.current_url:
            current_url = self.current_url
            self.play_music(current_url)

    def get_available_effects(self):
        """
        Get list of available audio effects
        
        Returns:
            list: Names of available effects
        """
        return ['nightcore', 'vaporwave', 'deep', '8bit']