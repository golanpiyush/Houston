import os
import logging
import threading
import time
import pygame
from colorama import Fore

# Initialize pygame mixer for audio
pygame.mixer.init()

def play_audio():
    """Play custom audio with pygame."""
    try:
        # Replace 'splashscreenaudio.mp3' with your audio file path
        pygame.mixer.music.load('audio/splashscreenaudio.mp3')  # Path to your audio file
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)  # Keep the program running until the audio finishes
    except Exception as e:
        print(f"Error playing audio: {e}")

def new_user_Setup():
    """Setup the username and handle the audio play."""
    # Creates the log file if it doesn't exist
    if not os.path.exists('houstonmemories.log'):
        open('houstonmemories.log', 'w').close()
    
    username = None
    username_set = False

    # Reads the existing log file to check for a username
    with open('houstonmemories.log', 'r') as file:
        for line in file:
            if line.startswith("Username:"):
                username = line.strip().split(": ")[1]
                username_set = True
                break
    
    if not username_set:
        # Asks for the username and saves it to the file
        username = input(f"{Fore.YELLOW}Enter your username: ")
        with open('houstonmemories.log', 'a') as file:
            file.write(f"Username: {username}\n")
        logging.info(f"Username set: {username}")
        print(f"{Fore.GREEN}Logging in as", f"{Fore.MAGENTA}{username}")
        
        # Ensure the login message is shown before playing the audio
        threading.Thread(target=delayed_audio_playback).start()
        time.sleep(7)  # Wait for a moment before playing the audio
        
        # Play audio after username is set
        
    else:
        print(f"{Fore.GREEN}Logging in as", f"{Fore.CYAN}{username}")
        
        
        # Play audio after 7-second delay, even if the username is set
        threading.Thread(target=delayed_audio_playback).start()

    return username

def delayed_audio_playback():
    """Delay the audio playback by 7 seconds."""
    play_audio()
    # time.sleep(7)

