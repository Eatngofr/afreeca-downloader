import time, os, requests, platform
from urllib.parse import urljoin
from requests.exceptions import ReadTimeout, ConnectionError

from tools.formatBytes import format_bytes
from tools.formatDuration import format_duration

from plugins.bigo.main import getPlaylist, getStreamData
from plugins.bigo.verify import concurrentVerify

usernameList = []

def downloadStream(instanceId, user, site):
  
  usernameList.insert(instanceId, [site, user, '', '', '', ''])
  
  segment_urls = set()

  if 'bigo' in site:
    usernameList[instanceId] = [site, user, '', '', '', '']

    if concurrentVerify(user) is True:
      file_size = 0
      start_time = time.time()
      m3u8Url = getPlaylist(user)
      siteId, nickname = getStreamData(user)
      
      # usernameList.append(['', '', '', '', '', ''])
      # usernameList.append([site, user, nickname, 'Starting', 'Starting', 'Starting'])
      if os.path.exists('downloads/Bigo/' + nickname) == False:
        os.makedirs('downloads/Bigo/' + nickname)

      now = time.strftime("%Y-%m-%d_%H:%M", time.localtime())
      if platform.system() == 'Windows':
        now = time.strftime("%Y-%m-%d_%H-%M", time.localtime())
      output_filename = nickname + '-' + siteId + '-' + now + '-bigo.ts'
      output_path = 'downloads/Bigo/' + nickname + '/' + output_filename
  
  while True:
      try:
        base_url = m3u8Url.rsplit('/', 1)[0] + '/'
        res = requests.get(m3u8Url)
        playlist_content = res.text

        new_segment_lines = [
          line.strip() for line in playlist_content.splitlines() if line.endswith('.TS') or line.endswith('.ts')
        ]

        if '.ts' not in playlist_content.lower():
          
          usernameList[instanceId] = [site, user, '', 'Offline', 'Offline', 'Offline']
          if 'bigo' in site:
            if concurrentVerify(user) is True:
              file_size = 0
              start_time = time.time()
              m3u8Url = m3u8Url = getPlaylist(user)
              now = time.strftime("%Y-%m-%d_%H:%M", time.localtime())
              if platform.system() == 'Windows':
                now = time.strftime("%Y-%m-%d_%H-%M", time.localtime())
              output_filename = nickname + '-' + siteId + '-' + now + '-bigo.ts'
              output_path = 'downloads/Bigo/' + nickname + '/' + output_filename
              continue
          with open(output_path, 'ab') as output_file:
          for new_segment_line in new_segment_lines:
            segment_url = urljoin(base_url, new_segment_line)
            if segment_url not in segment_urls:
              segment_urls.add(segment_url)
              try:
                res = requests.get(segment_url, timeout=15)
              except (ReadTimeout, ConnectionError):
                continue
              file_size += len(res.content)
              elapsed_time = time.time() - start_time
              output_file.write(res.content)
              usernameList[instanceId] = [site, user, nickname, format_bytes(file_size), format_duration(elapsed_time), output_filename]

      except (ReadTimeout, ConnectionError):
        continue
