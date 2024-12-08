import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
AudioSegment.converter = "C:/ffmpeg/ffmpeg/bin/ffmpeg.exe"
AudioSegment.ffmpeg = "C:/ffmpeg/ffmpeg/bin/ffmpeg.exe"
AudioSegment.ffprobe ="C:/ffmpeg/ffmpeg/bin/ffprobe.exe"
def convert_audio_to_text(audio_file_path):
    print(audio_file_path)
    try:
        # Преобразование OGG в WAV
        sound = AudioSegment.from_ogg(audio_file_path)
        sound.export(audio_file_path[:-4]+".wav", format="wav")
        audio_file_path = audio_file_path[:-4]+".wav" # Используем временный WAV файл


        r = sr.Recognizer()
        with sr.AudioFile(audio_file_path) as source:
            audio = r.record(source)
            text = r.recognize_google(audio, language="ru-RU")
            return text
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
    finally:
        try:
            import os
            os.remove(audio_file_path)
        except:
            pass

def audio_to_text(filename):
    print(filename)
    return convert_audio_to_text(filename)
