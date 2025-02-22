import requests
from plugins.afreeca.getPlaylist import getVideoPlaylist, getStationNo
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import os
import platform
from urllib.parse import urljoin
from tools.formatBytes import format_bytes
from tools.formatDuration import format_duration
from plugins.afreeca.verify import verify

def download(url, username):
  # attempt to alleviate dropped connections [NEEDS TESTING]
  session = requests.Session()
  retry = Retry(connect=5, backoff_factor=0.5)
  adapter = HTTPAdapter(max_retries=retry)
  session.mount('http://', adapter)
  session.mount('https://', adapter)
  cookie = open('cookies/afreeca', 'r').read().strip()
  headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/118.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate, br",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://play.afreecatv.com",
    "DNT": "1",
    "Alt-Used": "live.afreecatv.com",
    "Connection": "keep-alive",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "Sec-GPC": "1",
    "Cookie": cookie,
    "TE": "trailers",
  }

  base_url = url.rsplit('/', 1)[0] + '/'
  now = time.strftime("%Y-%m-%d_%H:%M", time.localtime())
  
  if platform.system() == 'Windows':
    now = time.strftime("%Y-%m-%d_%H-%M", time.localtime())

  output_filename = username + '-' + getStationNo(username,'') + '-' + now + '-afreeca.ts'

  output_path = 'downloads/Afreeca/' + username + '/' + output_filename

  if os.path.exists('downloads/Afreeca/' + username) is False:
      os.makedirs('downloads/Afreeca/' + username)

  segment_urls = set()

  file_size = 0
  start_time = time.time()

  while True:
    response = session.get(url, headers=headers)
    playlist_content = response.text

    if '<p>Sorry, the page you are looking for is currently unavailable.<br/>' in playlist_content:
        print("\nStream paused")
        time.sleep(60)
        continue

    # works for the most part, but needs testing
    if '<title>502 Server Error</title>' in playlist_content:
        print(f"\nStream finished. Exiting the program.")
        if verify(username):
            download(getVideoPlaylist(username, ''), username)

    new_segment_lines = [
        line.strip() for line in playlist_content.splitlines() if line.endswith('.TS') or line.endswith('.ts')
    ]

    with open(output_path, 'ab') as output_file:
        
        for new_segment_line in new_segment_lines:
            segment_url = urljoin(base_url, new_segment_line)
            if segment_url not in segment_urls:
                segment_urls.add(segment_url)
                response = session.get(segment_url)
                file_size += len(response.content)
                elapsed_time = time.time() - start_time
                output_file.write(response.content)
                print("\r" + f"Downloading to {output_filename} || {format_duration(elapsed_time)} @ {format_bytes(file_size)}             \x1b[?25l", end="", flush=True)

    time.sleep(3)

def downloadVod(url, output_filename, username):
   
  # attempt to remedy dropped connections, works i think ???/
  session = requests.Session()
  retry = Retry(connect=3, backoff_factor=0.5)
  adapter = HTTPAdapter(max_retries=retry)
  session.mount('http://', adapter)
  session.mount('https://', adapter)

  output_path = 'downloads/Afreeca/' + username + '/' + output_filename

  if os.path.exists('downloads/Afreeca/' + username) is False:
      os.makedirs('downloads/Afreeca/' + username)

  while True:
      headers = {}
      if os.path.exists(output_path):
          headers['Range'] = f'bytes={os.path.getsize(output_path)}-'

      res = session.get(url, stream=True)

      with open(output_path, 'ab') as output_file:
          for chunk in res.iter_content(chunk_size=1024):
              output_file.write(chunk)
              # does not include time as it is not a live stream, don't want to run mediainfo on every check
              if len(chunk) != 1024 and getStationNo(username, '') is False:
                  print('\nDownload complete.')
                  exit()
                  
              print("\r" + f"Downloading to {output_filename} || {format_bytes(os.path.getsize(output_path))}    \x1b[?25l", end="", flush=True)

      time.sleep(1)