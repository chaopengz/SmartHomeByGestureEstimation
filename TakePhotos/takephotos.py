import time
import cv2
from PIL import Image
import requests

import datetime


def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d,%H-%M-%S", local_time)
    data_secs = (ct - long(ct)) * 1000
    time_stamp = "%s-%03d" % (data_head, data_secs)
    return time_stamp


def takePhoto():
    while (True):
        camera_port = 0
        camera = cv2.VideoCapture(camera_port)
        time.sleep(0.3)  # If you don't wait, the image will be dark
        return_value, image = camera.read()
        time_stmp = get_time_stamp()
        file_name = time_stmp + '.jpg'
        cv2.imshow("capture", image)
        cv2.imwrite(file_name, image)
        file_name = compress_photo(file_name)
        upload_image(file_name)
        print file_name


def compress_photo(filename):
    img = Image.open(filename)
    w, h = img.size
    raito = float(w) / h
    new_height = 368
    new_width = int(new_height * raito)
    print w, h
    print new_width, new_height
    new_file_name = filename[0:-4] + '_small.jpeg'
    img.resize((new_width, new_height)).save('images/' + new_file_name)
    return new_file_name


def upload_image(filename):
    dir = '/Users/zhangchaopeng/PycharmProjects/TakePhotos/images/'
    url = 'http://219.223.194.246:8000/postPic/'
    filename = dir + filename
    files = {'image': open(filename, 'rb')}
    print requests.post(url, files=files)


if __name__ == '__main__':
    takePhoto()
