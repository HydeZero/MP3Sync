from genericpath import isdir
import os
import platform
import subprocess
import pdb
import shutil

from mutagen.id3 import ID3

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
    if (platform.system() == "Windows"):
        print("Please make sure ffmpeg\\bin is added to path. For best results, move the ffmpeg folder to C:\\. Otherwise you don't need to do anything at all.")
except Exception as e:
    print("PyDub was either not found or was unable to be imported. MP3 conversion will not be able to be used.")
    print(e)

try:
    from mutagen.flac import FLAC, Picture
    from mutagen.mp3 import MP3
    from mutagen.easyid3 import EasyID3
    from mutagen.id3 import ID3, APIC
except Exception as e:
    print("mutagen Not Found. Disabling conversion... (mutagen can get and write metadata from/to files)")
    isPydub = False

if (input(f"Is this your music library? {home}/Music/ [Y/n] ").lower() != "n"):
    musicLibrary = home+"/Music/"

print("Type any directories you want to exclude, separated by commas, NO SPACES BETWEEN ITEMS. If you don't want to exclude directories, just press enter.")

dirToExclude = input().split(",")

print("TYPE THE DIRECTORY WHERE YOUR MP3 PLAYER IS MOUNTED. WE WILL HANDLE EVERYTHING FROM HERE.")

mp3MountDir = input("FULL DIRECTORY TO MP3 PLAYER MOUNT POINT (/using/this/directory/structure). Forward slashes work on windows also.\n> ").replace("\\", "/")

print("Searching for files... Please hold...")

acceptableExtensions = ["mp3", "flac", "m4a"]

directs = []
def getDirs(direct):
    for item in os.listdir(direct):
        print(item)
        if not (item in dirToExclude):
            if os.path.isdir(direct + item):
                    directs.append(item)

getDirs(musicLibrary)

hostDirects = directs.copy()
curPath = musicLibrary

files = []

fileNum = 0

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
        processedFiles = 0
        bkupMp3Mount = mp3MountDir
        mp3MountDir = home + "/.mp3SyncTemp" #these two lines make conversion faster as it doesn't have to write directly to the MP3 player. We will copy all after.
        if not os.path.isdir(mp3MountDir):
            os.mkdir(mp3MountDir)
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
                    if not os.path.isdir(mp3MountDir + "/" + artist_dir):
                        os.mkdir(mp3MountDir + "/" + artist_dir)
                    os.mkdir(mp3MountDir + "/" + artist_dir + "/" + album_dir)

                save_dir = mp3MountDir + "/" + artist_dir + "/" + album_dir + "/"

                print(f"Saving file {file_path.name} as mp3...")

                flac_tmp_audio_data.export(save_dir + file_path.name.replace(file_path.suffix, "") + ".mp3", format="mp3", bitrate="320k")
                print("EXPORTED", file, "AS MP3")
                
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
                
                # Now we take the flac album cover and copy it over to the MP3, making it as complete as possible.

                output_metadata = MP3(save_dir + file_name, ID3=ID3) # We open the MP3 file with the full set of ID3 features, so we can add covers.

                art = source_metadata.pictures[0].data # Get source data art

                with open(save_dir + "temp_cover", "wb") as tempCover: # for mime identification
                    tempCover.write(art)
                    tempCover.close()

                import magic

                mime_type = magic.from_file(save_dir + "temp_cover", mime=True)

                output_metadata.tags.add(
                    APIC(
                        encoding=0,
                        mime=mime_type,
                        type=3,
                        desc=u'Cover',
                        data=art
                    )
                ) # Thank you Chunpin for the stack overflow question that perfectly described this

                output_metadata.save()

                os.remove(save_dir + "temp_cover")
            elif file.split(".")[-1] == "mp3":
                print(f"{file} is a MP3 file already. Copying...")
                file_path = PurePath(file)
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
                    if not os.path.isdir(mp3MountDir + "/" + artist_dir):
                        os.mkdir(mp3MountDir + "/" + artist_dir)
                    os.mkdir(mp3MountDir + "/" + artist_dir + "/" + album_dir)

                save_dir = mp3MountDir + "/" + artist_dir + "/" + album_dir + "/"

                shutil.copy2(file, save_dir)
            else:
                print("Your file isn't in a format we can convert yet. We will just copy it.")
                file_path = PurePath(file)
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
                    if not os.path.isdir(mp3MountDir + "/" + artist_dir):
                        os.mkdir(mp3MountDir + "/" + artist_dir)
                    os.mkdir(mp3MountDir + "/" + artist_dir + "/" + album_dir)

                save_dir = mp3MountDir + "/" + artist_dir + "/" + album_dir + "/"

                shutil.copy2(file, save_dir)
            processedFiles += 1
            print(f"Processed file {processedFiles} of {fileNum} ({processedFiles/fileNum}% done)")
    else:
        bkupMp3Mount = mp3MountDir
        mp3MountDir = home + "/Music"
    print("Conversion complete. Copying to MP3 Player... This may take a bit...")
    try:
        os.removedirs(bkupMp3Mount)
        shutil.copytree(mp3MountDir, bkupMp3Mount)
        try:
            os.remove(bkupMp3Mount + "/desktop.ini") #we don't need that on windows
        except Exception as e:
            pass #it may not exist
    except Exception as e:
        print("Something went wrong...")
        if str(e).split("]")[0] == "[WinError 183":
            print("Looks like we couldn't copy due to an existing directory/directories there. Please delete the Music folder on your mp3 player and start again.")
        elif str(e).split("]")[0] == "[WinError 5":
            print("We couldn't access", str(e).split()[-1] + ".", "Please make sure you have access rights.")