import pytube
import dailymotion
url = 'https://www.youtube.com/watch?v=4SFhwxzfXNc'

youtube = pytube.YouTube(url)
video = youtube.streams.first()
video.download('/videos')
print('DD')

d = dailymotion.Dailymotion()
d.set_grant_type('password', api_key='e77e051ea778bc4aca2d', api_secret='0631154017842010aa4796fa23ee0aa6a167514a',
    scope=['userinfo'], info={'username': USERNAME, 'password': PASSWORD})
url = d.upload('./video/top5.mp4')
print('ok')
d.post('/me/videos',
    {'url': url, 'title': 'Demo', 'published': 'true', 'channel': 'Demo'})