import moviepy.editor as mp
import cv2
import os
from pydub import AudioSegment
from Speech import stt


def detect_colored_square(frame):
    image = cv2.imread(frame)
    image = image[200: -200, :]  # remove recording flickering indication

    # manipulating image to easily detect squares
    blur = cv2.GaussianBlur(image, (7, 7), 1)
    gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    canny = cv2.Canny(gray, 22, 23)

    # Two pass dilate with horizontal and vertical kernel
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 5))
    dilate = cv2.dilate(canny, horizontal_kernel, iterations=2)
    vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 9))
    dilate = cv2.dilate(dilate, vertical_kernel, iterations=2)

    # Find contours, filter using contour threshold area, and draw rectangle
    cnts = cv2.findContours(dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]
    color = None
    for c in cnts:
        area = cv2.contourArea(c)
        if area > 20000:
            x, y, w, h = cv2.boundingRect(c)
            cv2.rectangle(image, (x, y), (x + w, y + h), (36, 255, 12), 3)
            colored_square = image[y + 100: y + h - 100, x + 100: x + w - 100]
            color = colored_square
    cv2.imshow('image', image)
    return color  # returns a ndarray of brg pixels


def delete_image(file_loc):
    try:
        os.remove(file_loc)
    except FileExistsError:
        print(f"Oh my! theres no file at {file_loc}")


class ExperimentFile:
    def __init__(self, file_location: str, file_name: str):
        self.location = file_location
        self.name = file_name.replace(".mov", "")
        self.video_file = mp.VideoFileClip(fr"{self.location}")
        self.audio_location = "audio/"
        self.video_location = "video/"
        self.color = None
        self.all_colors = dict()
        self.color_count = 0
        self.fps = self.video_file.subclip(0, 10).fps
        self.stt = stt.AudioFile

    def get_audio(self):
        path = os.path.join(self.audio_location, f"{self.name.replace('mov', '')}.mp3")
        if not os.path.exists(path):
            print(f"{self.name}, exists. \n not rewriting data")
            self.video_file.audio.write_audiofile(fr"{self.audio_location}{self.name}.mp3")
        return path

    def get_video(self):
        new_clip = self.video_file.without_audio()
        new_clip.write_videofile(f"{self.video_location}{self.name}.mov", codec="libx264")

    def read_frames(self):
        vidcap = cv2.VideoCapture(self.location)
        start_frame_number = 100
        vidcap.set(cv2.CAP_PROP_POS_FRAMES, start_frame_number)
        success, image = vidcap.read()
        cv2.imshow('image', image)
        count = 0
        frame_num = start_frame_number + count
        success = True
        while success:
            success, image = vidcap.read()
            vidcap.set(cv2.CAP_PROP_POS_FRAMES, frame_num + 30)
            count = frame_num + 30
            frame_num += 30
            if image is None:
                return
            cv2.imwrite(f"images/{self.name}_frame_{frame_num}.jpg", image)
            sqr = detect_colored_square(f"images/{self.name}_frame_{frame_num}.jpg")
            if sqr is None:  # if no colored square was detected
                delete_image(f"images/{self.name}_frame_{frame_num}.jpg")
                continue
            to_hex = '#%02x%02x%02x' % (sqr[0][0][2], sqr[0][0][1], sqr[0][0][0])
            self.handle_square(to_hex, sqr, frame_num)

    def handle_square(self, hexed_color, sqr, frame_count):
        if not self.color_count:
            self.color_count += 1
            self.color = hexed_color
            self.all_colors[str(self.color)] = self.add_color(frame_count)
            cv2.imwrite(f"squares/{self.name}_frame_{frame_count}.jpg", sqr)
            delete_image(f"images/{self.name}_frame_{frame_count}.jpg")
            return
        if str(self.color_count) in self.all_colors.keys():
            delete_image(f"images/{self.name}_frame_{frame_count}.jpg")
            return
        if self.color != hexed_color:
            self.all_colors[str(self.color)]["end_frame"] = frame_count - 1
            self.all_colors[str(self.color)]["end_ts"] = (frame_count - 1) / self.fps
            audio = self.split_audio(self.all_colors[str(self.color)]["start_ts"],
                                     self.all_colors[str(self.color)]["end_ts"],
                                     f"color_num_{self.color_count}--{self.color}")
            stt_chunk = self.stt(f"{self.audio_location}temp/color_num_{self.color_count}--{self.color}", "iw-IL")
            stt_chunk.upload_file()
            stt_chunk.configure()
            text = stt_chunk.transcribe()
            self.all_colors[str(self.color)]["transcript"] = [
                (result.alternatives[0].transcript, result.alternatives[0].confidence) for result in text.results]
            for result in text.results:
                print(result)
                print(result.alternatives[0].transcript)
                print(result.alternatives[0].confidence)
                print()
            self.color_count += 1
            self.color = hexed_color
            self.all_colors[str(self.color)] = self.add_color(frame_count)
            cv2.imwrite(f"squares/{self.name}_frame_{frame_count}.jpg", sqr)
            delete_image(f"images/{self.name}_frame_{frame_count}.jpg")
            return

    def add_color(self, frame_count):
        item = {
            "color": self.color,
            "start_frame": frame_count,
            "end_frame": None,
            "start_ts": frame_count / self.fps,
            "end_ts": None,
            "color_num": self.color_count
        }
        print(f"added color {self.color} number {self.color_count}")
        return item

    def get_all_colors(self):
        return self.all_colors

    def split_audio(self, start, end, split_filename):
        audio = AudioSegment.from_mp3(f"{self.audio_location}{self.name}.mp3")
        split_audio = audio[start * 1000:end * 1000]
        split_audio.export(self.audio_location + 'temp' + '/' + split_filename + '.mp3', format="wav")
        return split_audio
