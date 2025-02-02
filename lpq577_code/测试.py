import requests


url = 'https://www.jumia.com.ng/generic-1080p-lens-car-digital-video-recorder-dvr-camera-monitor-dash-cam-recorder-rearview-mirror-114514571.html'
result = requests.get(url)
print(result.text)