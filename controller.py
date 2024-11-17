import time
from itertools import cycle
from rich.console import Console
from rich.panel import Panel
from rich.style import Style
from rich.progress import Progress, SpinnerColumn, TextColumn
import re
import threading

# Regular expression for YouTube URLs
youtube_link_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'

class MusicPlayerConsole:
    def __init__(self, player, username):
        self.player = player
        self.username = username
        self.looper = False
        self.rotating_cd = cycle(["💿"])
        self.current_title = "Nothing's Playing?"
        self.status = "Stopped"
        self.console = Console()
        self.running = True
        self.command_timer = None  # Timer to disable pause/resume after a time
        self.last_command_time = time.time()

    def append_to_console(self, message):
        """Display messages to the console."""
        self.console.print(f"[System]: {message}")

    def display_now_playing(self):
        """Show the rotating CD and now playing info."""
        self.console.clear()
        cd = next(self.rotating_cd)
        loop_status = "[bold green]Loop Enabled[/bold green]" if self.looper else ""
        username_display = f"User -> [bold cyan]{self.username}[/bold cyan]"

        # If loop is enabled, we move the username to the right of the status
        if self.looper:
            status_message = f"{cd} Now Playing: [bold cyan]{self.current_title}[/bold cyan]  {loop_status}  {username_display}"
        else:
            status_message = f"{cd} Now Playing: [bold cyan]{self.current_title}[/bold cyan]  Status: [bold green]{self.status}[/bold green]  {username_display}"

        self.console.print(
            Panel(
                status_message,
                title="[bold yellow]DARA[/bold yellow]",
            )
        )

    def handle_command(self, command):
        """Handle user commands."""
        if command in ["pause", "p"]:
            self.pause_music()
        elif command in ["resume", "r"]:
            self.resume_music()
        elif command in ["loop", "l"]:
            self.start_loop()
        elif command in ["breakloop", "le"]:
            self.stop_loop()
        elif command in ["stop", "s"]:
            self.stop_music()
        elif command in ["quit", "q"]:
            self.append_to_console("Exiting the music player...")
            exit(0)
            # self.running = False
            
        elif re.match(youtube_link_regex, command) or command:
            self.play_music(command)
        else:
            self.append_to_console("Unknown command. Try 'pause', 'resume', 'stop', or 'quit'.")

    def play_music(self, query):
        """Play music based on the query."""
        self.append_to_console(f"Playing: {query}")
        self.status = "Playing"
        audio_url, title = self.player.get_audio_info(query)
        if audio_url:
            self.current_title = title
            self.player.play_music(audio_url)
            self.append_to_console(f"Now Playing: {title}")
            self.simulate_progress()  # Simulate a progress bar
        else:
            self.append_to_console("Failed to retrieve audio URL.")

    def pause_music(self):
        """Pause the music."""
        self.player.pause_music()
        self.status = "Paused"
        self.append_to_console("Music paused.")
        self.disable_pause_resume()

    def resume_music(self):
        """Resume the music."""
        self.player.resume_music()
        self.status = "Playing"
        self.append_to_console("Music resumed.")
        self.disable_pause_resume()

    def start_loop(self):
        """Start looping the current track."""
        self.looper = True
        self.player.loop = True
        self.append_to_console("Looping enabled.")
        self.display_now_playing()  # Update the display immediately when loop starts

    def stop_loop(self):
        """Stop looping the current track."""
        self.looper = False
        self.player.loop = False
        self.append_to_console("Looping disabled.")
        self.display_now_playing()  # Update the display immediately when loop stops

    def stop_music(self):
        """Stop playing music."""
        self.player.stop_music()
        self.status = "Stopped"
        self.current_title = "Nothing's Playing?"
        self.append_to_console("Music stopped.")

    def simulate_progress(self):
        """Simulate a progress bar for song playback."""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task(f"Playing: {self.current_title}", total=100)
            for _ in range(100):
                time.sleep(0.1)  # Simulate playback time
                progress.update(task, advance=1)

    def disable_pause_resume(self):
        """Disable 'pause' and 'resume' after some time."""
        if self.command_timer:
            self.command_timer.cancel()  # Cancel any previously scheduled timer
        self.command_timer = threading.Timer(5, self.remove_pause_resume)
        self.command_timer.start()

    def remove_pause_resume(self):
        """Hide pause and resume commands after 5 seconds."""
        self.append_to_console("The 'pause' and 'resume' commands are now disabled until the next song starts.")
        self.last_command_time = time.time()

    def run(self):
        """Run the main loop of the console music player."""
        self.console.print("[bold green]Welcome to the Music Player![/bold green]")
        self.append_to_console("Type a song name, YouTube link, or commands like 'pause', 'resume', 'stop', or 'quit'.")
        while self.running:
            self.display_now_playing()
            command = self.console.input("[italic bold magenta]Enter command:[/] ").strip()
            self.handle_command(command)

# Control function
def control_music(player, username):
    console_player = MusicPlayerConsole(player, username)
    console_player.run()
