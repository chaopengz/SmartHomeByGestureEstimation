import requests

url = 'http://127.0.0.1:8000/postPic/'
files = {'image': open('D:\Download\pa20120502330.jpg', 'rb')}
requests.post(url, files=files)
