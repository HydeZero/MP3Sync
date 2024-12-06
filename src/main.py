from genericpath import isdir
import os
import platform
import subprocess
import pdb

if input("show license? [y/N] ").lower() == "y":
    with open ("LICENSE", "r") as license_text:
        print(license_text.read())

try:
    from pathlib import PurePath
except Exception as e:
    print("UNABLE TO GET pathlib. Quitting...")
    print(e)
    quit()

isPydub = False

if (platform.system() == "Linux"):
    home=os.environ['HOME']
elif (platform.system() == "Windows"):
    home=os.environ['UserProfile'].replace("\\","/")

# Get (optional) pydub.
# TODO: See if conversion works without 
try:
    from pydub import AudioSegment
    isPydub = True
    print("Please make sure ffmpeg is in C:\\ffmpeg and that C:\\ffmpeg is in. Otherwise you don't need to do anything at all.")
except Exception as e:
    print("PyDub was either not found or was unable to be imported. MP3 conversion will not be able to be used.")
    print(e)

try:
    from mutagen.flac import FLAC
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
except Exception as e:
    print("mutagen Not Found. Disabling conversion... (mutagen can get and write metadata from/to files)")
    isPydub = False

if (input(f"Is this your music library? {home}/Music/ [Y/n]").lower() != "n"):
    musicLibrary = home+"/Music/"

print("Type any directories you want to exclude, separated by commas, NO SPACES BETWEEN ITEMS.")

dirToExclude = input().split(",")

print("TYPE THE DIRECTORY WHERE YOUR MP3 PLAYER IS MOUNTED. WE WILL HANDLE EVERYTHING FROM HERE.")

mp3MountDir = input("FULL DIRECTORY TO MP3 PLAYER MOUNT POINT (/using/this/directory/structure/). Forward slashes work on windows also.\n> ").replace("\\", "/")

print("Searching for files... Please hold...")

acceptableExtensions = ["mp3", "flac", "m4a"]

directs = []
def getDirs(direct):
    for item in os.listdir(direct):
        print(item)
        if not (item in dirToExclude):
            try:
                if item.split(".")[1] != "???":
                    pass
            except:
                directs.append(item)

getDirs(musicLibrary)

hostDirects = directs.copy()
curPath = musicLibrary

files = []

fileNum = 1

for director in hostDirects:
    if director == "Playlists":
        continue
    for item in os.listdir(curPath + director):
        curPath = musicLibrary + director
        if item.split(".")[-1] != "jpg":
            if os.path.isdir(curPath + "/" + item):
                for item2 in os.listdir(curPath + "/" + item):
                    if item2.split(".")[-1] in acceptableExtensions:
                        print(f"Got item {fileNum}")
                        fileNum += 1
                        files.append(curPath + "/" + item + "/" + item2)
    curPath = musicLibrary

print("Got files.")

try:
    os.mkdir(mp3MountDir + "/" + "Music")
    mp3MountDir = mp3MountDir + "/" + "Music"
except:
    mp3MountDir = mp3MountDir + "/" + "Music"

if isPydub:
    if input("Convert files to MP3 format? This may take a while, depending on the processing speed. [y/N] ").lower() == "y":
        for file in files:
            if file.split(".")[-1] == "flac":
                file_path = PurePath(file)

                flac_tmp_audio_data = AudioSegment.from_file(file_path, file_path.suffix[1:])
                
                path_as_str = os.fspath(file_path)

                try:
                    artist_dir = path_as_str.split("/")[-3]
                except IndexError:
                    artist_dir = path_as_str.split("\\")[-3]
                
                try:
                    album_dir = path_as_str.split("/")[-2]
                except IndexError:
                    album_dir = path_as_str.split("\\")[-2]

                if not os.path.isdir(mp3MountDir +  "/" + artist_dir + "/" + album_dir):
                    os.mkdir(mp3MountDir + "/" + artist_dir)
                    os.mkdir(mp3MountDir + "/" + artist_dir + "/" + album_dir)

                save_dir = mp3MountDir + "/" + artist_dir + "/" + album_dir + "/"

                print(f"Saving file {file_path.name} as mp3...")

                flac_tmp_audio_data.export(save_dir + file_path.name.replace(file_path.suffix, "") + ".mp3", format="mp3", bitrate="320k")
                print("EXPORTED", file, "AS MP3, COPYING METADATA")
                
                file_name = file_path.name.replace(file_path.suffix, "") + ".mp3"

                source_metadata = FLAC(file)

                output_metadata = EasyID3(save_dir + file_name)
                
                # Copy the main data over (album, title, artist, release, track number, etc.)

                output_metadata["title"] = source_metadata["TITLE"]

                output_metadata["album"] = source_metadata["ALBUM"]

                output_metadata["tracknumber"] = source_metadata["TRACKNUMBER"]

                output_metadata["artist"] = source_metadata["ARTIST"]

                output_metadata["date"] = source_metadata["DATE"]

                output_metadata["genre"] = source_metadata["GENRE"]

                output_metadata.save() # we're done here
                
                # Now we take the flac album cover and copy it over to the MP3, making it as complete as possible

                # TODO: Add album cover copying mechanism
