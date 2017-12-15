import requests
import time
from PIL import Image


def get_time_stamp():
    ct = time.time()
    local_time = time.localtime(ct)
    data_head = time.strftime("%Y-%m-%d,%H-%M-%S", local_time)
    data_secs = (ct - long(ct)) * 1000
    time_stamp = "%s-%03d" % (data_head, data_secs)
    return time_stamp


def compress_photo(filename):
    img = Image.open(filename)
    w, h = img.size
    raito = float(w) / h
    new_height = 368
    new_width = int(new_height * raito)
    print w, h
    print new_width, new_height
    new_file_name = filename[0:-4] + '_small.jpeg'
    print new_file_name
    img.resize((new_width, new_height)).save(new_file_name)
    return new_file_name


def upload():
    url = 'http://219.223.196.151:8000/postPic/'
    filename = 'F:\OOAD\SmartHomeByGestureEstimation\Server\web\sample_image\\1.jpg'
    filename = compress_photo(filename)
    files = {'image': open(filename, 'rb')}
    print get_time_stamp()
    response = requests.post(url, files=files)
    print response.content
    print get_time_stamp()


if __name__ == '__main__':
    upload()
