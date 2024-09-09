import os
import time
from colored import Fore
from music_player import MusicPlayer
import syncedlyrics
import threading

def clear_screen():
    print("\033[H\033[J", end="")



def control_music(player):
    try:
        while True:
            if not player.is_playing:
                command = input(f"{Fore.BLACK}Enter command (play [song name]/quit): ").lower()
                if command.startswith('play '):
                    song_name = command[5:]
                    print(f"{Fore.GREEN}Finding the song...")
                    if not song_name.endswith('audio'):
                        song_name += ' audio'
                    audio_url, title = player.get_audio_info(song_name)
                    if audio_url:
                        print(f"{Fore.BLACK}Streaming: {title}") 
                        player.is_playing = True 
                        player.play_music(audio_url)
                        # threading.Thread(target=display_synced_lyrics, args=(player, song_name), daemon=True).start()
                    else:
                        print("Failed to retrieve the streamable audio URL.")
                # elif command == 'lyrics':
                #     song_name = input("Enter the song name: ")  
                #     threading.Thread(target=display_synced_lyrics, args=(player, song_name), daemon=True).start()
                elif command == 'quit':
                    print("Exiting music player.")
                    player.stop_music()
                    break
                else:
                    print(f"{Fore.RED}Unknown command.")
                    time.sleep(2)
                    print(f'{Fore.WHITE} Usage example : "play [song name]"')
            else:
                command = input(f"{Fore.BLACK}Enter command (pause/resume/loop/breakloop/download/stop/quit): ").lower()
                if command == 'pause' or command == 'p':
                    player.pause_music()
                elif command == 'resume' or command == 'r':
                    player.resume_music()
                elif command == 'loop' or command == 'l':
                    player.loop = True
                    print(f"{Fore.GREEN}Loop started.")
                    if player.loop_thread is None or not player.loop_thread.is_alive():
                        player.loop_thread = threading.Thread(target=player._loop_music, name='MusicLooper', daemon=True)
                        player.loop_thread.start()
                elif command == 'download' or command == 'dwn':
                    player.downloader()
                elif command == 'breakloop' or command == 'le':
                    player.loop = False
                    print(f"{Fore.RED}Loop terminated.")
                elif command == 'stop' or command == 's':
                    player.stop_music()
                elif command == 'now':
                    print(f"{Fore.white}Streaming: {title}") 
                elif command == 'quit' or command == 'q':
                    player.stop_music()
                    print(f"{Fore.WHITE}Exiting music player.")
                    break
                else:
                    print(f"{Fore.RED}Unknown command.")
    except KeyboardInterrupt:
        player.stop_music()
        print("\nExiting music player due to KeyboardInterrupt.")

if __name__ == "__main__":
    player = MusicPlayer()
    control_music(player)


# def display_synced_lyrics(player, song_name):
#     synced_lyrics = syncedlyrics(song_name)  # Corrected function call
#     if synced_lyrics:
#         current_index = 0
#         while current_index < len(synced_lyrics):
#             lyric1 = synced_lyrics[current_index].text
#             duration1 = synced_lyrics[current_index].duration
#             if current_index + 1 < len(synced_lyrics):
#                 lyric2 = synced_lyrics[current_index + 1].text
#                 duration2 = synced_lyrics[current_index + 1].duration
#             else:
#                 lyric2 = ''
#                 duration2 = 0

#             print(f"{Fore.CYAN}Synced Lyrics:")
#             print(f"{lyric1}\n{lyric2}")
#             time.sleep(min(duration1, duration2))
#             clear_screen()
#             current_index += 2
