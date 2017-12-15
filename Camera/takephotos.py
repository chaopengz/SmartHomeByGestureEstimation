import time
import cv2
from PIL import Image
import requests

import datetime


class Camera(object):
    def __init__(self):
        self.filename = ""
        self.time_stamp = ""
        self.small_filename = ""
        self.postUrl = ""
        self.baseDir = ""

    def set_time_stamp(self):
        ct = time.time()
        local_time = time.localtime(ct)
        data_head = time.strftime("%Y-%m-%d,%H-%M-%S", local_time)
        data_secs = (ct - long(ct)) * 1000
        time_stamp = "%s-%03d" % (data_head, data_secs)
        self.time_stamp = time_stamp

    def takePhotos(self):
        while (True):
            camera_port = 0
            camera = cv2.VideoCapture(camera_port)
            time.sleep(0.3)  # If you don't wait, the image will be dark
            return_value, image = camera.read()

            self.set_time_stamp()
            self.filename = self.time_stamp + '.jpg'
            cv2.imwrite(self.filename, image)

            self.compress_photo()
            self.upload_image()

    def compress_photo(self):
        img = Image.open(self.filename)
        w, h = img.size
        # raito = float(w) / h
        new_height = 272  # 368
        new_width = 368  # int(new_height * raito)
        print w, h
        print new_width, new_height
        self.small_filename = self.filename[0:-4] + '_small.jpeg'
        img.resize((new_width, new_height)).save('images/' + self.small_filename)

    def upload_image(self):
        pathname = self.baseDir + self.filename
        files = {'image': open(pathname, 'rb')}
        response = requests.post(self.postUrl, files=files)
        print response.content

    def setPostUrl(self, url):
        self.postUrl = url

    def setBaseDir(self, base_dir):
        self.baseDir = base_dir


if __name__ == '__main__':
    camera = Camera()
    camera.setBaseDir('/Users/zhangchaopeng/PycharmProjects/TakePhotos/images/')
    camera.setPostUrl('http://219.223.196.151:8000/postPic/')
    camera.takePhotos()
