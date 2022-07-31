import json
import os
from google.cloud import speech
from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "clients/allcolors-357013-42addf60ad3c.json"


class AudioFile:
    def __init__(self, media: str, lang: str, punctuation: bool = True, sample_rate: int = 48000, enhance: bool = True,
                 model: str = 'video'):
        self.client = speech.SpeechClient()
        self.file = media
        self.filename = self.file.split("/")[1]
        self.lang_code = lang
        self.punctuation = punctuation
        self.enhance = enhance
        self.sample_rate = sample_rate
        self.model = model
        self.audio_file = None
        self.config_wav = None
        self.audio_wav = None
        self.gcs_url = "gs://all_colors_speech_to_text/"

    def configure(self):
        print("configuring")
        url = self.gcs_url + self.filename
        print(url)
        self.audio_file = speech.RecognitionAudio(uri=url)
        self.config_wav = speech.RecognitionConfig(
            sample_rate_hertz=self.sample_rate,
            enable_automatic_punctuation=self.punctuation,
            language_code=self.lang_code,
            use_enhanced=self.enhance,
            model=self.model
        )
        print("done configuring")

    def upload_file(self):
        print("uploading")
        creds = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
        with open(creds, "r") as text_file:
            credentials_content = json.load(text_file)
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(credentials_content)
        client = storage.Client(credentials=credentials, project='AllColors')
        bucket = client.get_bucket('all_colors_speech_to_text')
        blob = bucket.blob(f"{self.filename}")
        blob.upload_from_filename(f"{self.file}.mp3")
        print("uploaded")

    def transcribe(self) -> dict:
        config_wav = speech.RecognitionConfig(
            sample_rate_hertz=44100,
            enable_automatic_punctuation=True,
            language_code=self.lang_code,
            audio_channel_count=2
        )
        print("transcribing")
        audio_loc = f"gs://all_colors_speech_to_text/{self.filename}"
        print(f"location {audio_loc}")
        wav = speech.RecognitionAudio(uri=audio_loc)
        op = self.client.long_running_recognize(config=config_wav, audio=wav)
        print(op.result().results)
        return op.result(timeout=90)
