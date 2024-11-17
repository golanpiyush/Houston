from controller import MusicPlayerConsole  #
from music_player import MusicPlayer  

def main():
    from newuser_manager import new_user_Setup  

    player = MusicPlayer()

    username = new_user_Setup()  

    console = MusicPlayerConsole(player, username)

    while True:
        console.run()

if __name__ == "__main__":
    main()
