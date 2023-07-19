import os
import numpy as np
from pydub import AudioSegment
import moviepy.editor as mp
import json
import io
import time

# TODO: Change so that I read in the vosk model at _init_ and then split up the audio into chunks to clean
class Plex:
    """Plex class to clean words for any video"""
    def __init__(self, movie_path):
        self.movie_path = movie_path
        self.audio_path = None
        self.video_clip = mp.VideoFileClip(movie_path)
        self.audio_clip = None  # MoviePy object
        self.audio = None       # AudioSegment Object
        self.dictionary = None
        self.timestamps = None

    def extract_audio(self, audio_path="my_results.mp3"):
        self.audio_path = audio_path
        self.audio_clip = self.video_clip.audio
        self.video_clip.audio.write_audiofile(self.audio_path)
        return self.audio_clip

    def extract_text(self, audio_path=None):
        """Use STT to get dictionary of words and time stamp"""
        from vosk import Model, KaldiRecognizer

        model_path = "Models/vosk-model-en-us-0.22"
        model = Model(model_path)
        if audio_path is None:
            audio_path = self.audio_path

        self.audio = AudioSegment.from_file(audio_path)

        rec = KaldiRecognizer(model, self.audio.frame_rate*self.audio.channels)
        rec.SetWords(True)

        # get the list of JSON dictionaries
        results = []
        # data = self.audio.raw_data
        k = 1
        while True:
            frames = self.audio[(k-1)*20000:k*20000] # 20 Seconds
            data = frames.raw_data

            if data == b"":
                break

            rec.AcceptWaveform(data)

            result_dict = json.loads(rec.Result())
            if "result" in result_dict:
                results.append(result_dict)
            k += 1

        # self.dictionary = part_result
        self.results = results

        return self.results

    def clean_text(self, dictionary=None):
        """Find time stamps of naughty words to silence out"""
        if dictionary is None:
            dictionary = self.dictionary

        naughty_words = ["Fuck",
                         "Fuck you",
                         "Fucks",
                         "Fucking",
                         "Fucked",
                         "Fuckwit",
                         "Shitbag",
                         "Shit",
                         "Shitty",
                         "Shits",
                         "Piss off"
                         "Asshole",
                         "Ass",
                         "Dickweed",
                         "Dick",
                         "Son of a bitch",
                         "Bastard",
                         "Bitch",
                         "bitches",
                         "Bitchtits",
                         "Damn",
                         "Bloody hell",
                         "Choad",
                         "Pissflaps",
                         "Wanker",
                         "Piss",
                         "Arsebadger",
                         "Jizzcock",
                         "Cumdumpster",
                         "Shitmagnet",
                         "Dickhead",
                         "Shitpouch",
                         "Pisskidney",
                         "Cumwipe",
                         "Pisswizard",
                         "Cuntpuddle",
                         "Dickweasel",
                         "Cockwomble",
                         "Dickfucker",
                         "Wankface",
                         "Shithouse",
                         "Jizzbreath",
                         "Todger",
                         "Oh my God"]
        # naughty_words = ["Bryant", "hate", "love"] # Most recent naughty_words list will be used to filter

        naughty_words = [x.casefold() for x in naughty_words]
        time_stamps = []

        for r in self.results:
            for result in r["result"]:
                if result["word"].casefold() in naughty_words and result["conf"] > .5:
                    print(result["word"], result["start"])
                    time_stamps.append((result["start"], result["end"]))

        self.timestamps = time_stamps
        return time_stamps

    def clean_audio(self, time_stamps=None):
        """Take naughty word timestamps and use pydub to create silence in place of word"""
        if time_stamps is None:
            time_stamps = self.timestamps
        new_audio = self.audio

        for time_stamp in time_stamps:

            duration = time_stamp[1]-time_stamp[0]
            silence = AudioSegment.silent(duration*1000+50) # 50 for crossfade
            # new_audio = new_audio[0:time_stamp[0]*1000] + silence + self.audio[time_stamp[1]*1000:]

            # Crossfaded
            new_audio = new_audio[0:time_stamp[0]*1000].append(silence, crossfade=50).append(self.audio[time_stamp[1]*1000:], crossfade=50)

        new_audio.export("clean_audio.mp3")

        self.new_audio = new_audio

        return new_audio

    def clean_video(self, audiopath=None, new_movie_path = False):
        """Overlay new audio on top of original video"""
        if audiopath is not None:
            audioclip = mp.AudioFileClip(audiopath)
        else:
            assert(self.audio is not None)

            audioclip = mp.AudioFileClip("clean_audio.mp3")  # TODO: Throwing an error here

        new_audioclip = mp.CompositeAudioClip([audioclip])
        self.video_clip.audio = new_audioclip

        if new_movie_path:
            movie_path = self.movie_path[:-4] + "-Clean.mp4"
            self.video_clip.write_videofile(movie_path)
        else:
            self.video_clip.write_videofile(self.movie_path)
        os.remove("clean_audio.mp3")
        # os.remove("")
        pass

    def clean(self):
        self.extract_audio()
        print("Extracted Audio")
        self.extract_text()
        print("Ran Speech Diarization")
        self.clean_text()
        print("Filtered text")
        self.clean_audio()
        print("Cleaned audio track")
        self.clean_video(new_movie_path=True)
        print("Complete")
        pass


if __name__ == "__main__":

    # import glob
    #
    # movies = glob.glob("D:/*/*.mp4") + glob.glob("D:/*/*/*.mp4") + glob.glob("D:/*/*/*/*.mp4")
    # movies2 = glob.glob("D:/*/*.m4v") + glob.glob("D:/*/*/*.m4v") + glob.glob("D:/*/*/*/*.m4v")
    # movies3 = glob.glob("D:/*/*.avi") + glob.glob("D:/*/*/*.avi") + glob.glob("D:/*/*/*/*.avi")
    #
    # movies = movies + movies2 + movies3
    #
    # i = 1
    # for movie in movies:
    #
    #     start = time.time()
    #     plex = Plex(movie)
    #     plex.clean()
    #     print("SECONDS:", time.time()-start)
    #     print(f"Completed {i} of {len(movies)}")
    #     i += 1
    #     if i==2:
    #         break

    movie = "D:\\2. MOVIES\\H\\Hot Rod.mp4"
    # clip = "C:\\Users\\bryan\\Documents\\Python Scripts\\shortNelson_out.mp4"
    plex = Plex(movie)
    plex.clean()


    pass
