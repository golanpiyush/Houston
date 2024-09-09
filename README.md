# Houston
one of a music player kind uses cli
# Houston

## A Python-based CLI Script with Downloading and Streaming Capabilities :fa-headphones:  :fa-volume-up:


>  **Houston** is a command-line interface **(CLI)** script built in Python that allows users to stream, control, and download music from **YouTube Andriod Music** Databases. It utilizes yt_dlp for getting the stream links and uses mpv in the background and for playing audio.


 > **Features**:

> > :fa-check: Play Music: Stream music from URLs.
:fa-check: Pause/Resume: Control playback with ease.
:fa-check: Loop Mode: Enable or disable looping of the current track.
:fa-check: Download Music: Download and save audio files in various formats.
:fa-times: Sync Lyrics: Optional feature to display synced lyrics (functionality commented out).
:fa-check: Cross-platform Support: Works on Windows, macOS, and Linux.


> **Tech Stack**

>> :fa-drupal: Python: Programming language used for development.
:fa-drupal: yt_dlp: YouTube-DL fork for downloading audio and video.
:fa-drupal: mpv: Media player for playback.
:fa-drupal: logging: For handling application logs.
:fa-drupal: threading: For managing background tasks like looping music.


>**Installation: **
**Clone the Repository :fa-glass:**

>> bash
git clone https://github.com/golanpiyush/music-player.git
cd music-player

>**Install Dependencies:
**
>> bash
pip install -r requirements.txt
Download mpv:

>>**For Windows**: Download .exe or .msi from release page.
**For macOS and Linux**: Install via package managers.

>Run the Application:


> **Development:**
>>To contribute, follow the steps underneath:

>**Set Up Development Environment:
**
>>**bash**
>>pip install -r requirements.txt
Run the Application:

>>**bash**
python control.py
Run Tests (if applicable):

>>**bash**
pytest
Build (if applicable):
**
> LicenseLicense
MIT License. Check the LICENSE file for details.**

**Free Software, Hell Yeah!**
