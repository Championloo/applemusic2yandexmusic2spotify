import telebot
import threading
import re
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
from pprint import pprint
from yandex_music import Client as YMClient

#если бот в чате, ему нужны админские права, чтобы видеть сообщения
token = '0000000000:AAAAAAAAAAAAAAAAAABBBBBBBBBB'
bot = telebot.TeleBot(token)

@bot.message_handler(content_types=['text'])
def text(message):
	if 'https://music.apple.com' in message.text:
		# print(message.text)
		resp = requests.get(message.text, verify=False).text
		soup = BeautifulSoup(resp, 'lxml')
		ex = 0
    # определяем музыканта [ ,альбом] [, название композиции]
		try:
			musician = ' '.join(soup.find('div', {'class': 'product-creator typography-large-title'}).text.strip().split())
		except: 
			musician = ' '.join(soup.find('h1', {'class': 'typography-header-emphasized artist-header__product-title-product-name artist-header__product-title-product-name--non-persistent-color'}).text.strip())
		try:
			album = ' '+soup.find('h1', {'class': 'product-name typography-large-title-semibold clamp-4'}).text.strip()
		except: album = ''
		try:
			select_track = ' '+soup.find('div', {'aria-checked': 'true'}).text.strip()
			tracks = soup.find_all('div', {'class': 'songs-list-row songs-list-row--selected selected songs-list-row--web-preview web-preview songs-list-row--song'})
			for i in tracks:
				if 'aria-checked="true"' in str(i):
					index = int(i['data-row'])
      #если мы даём ссылку на конкретную композицию, то скачаем и отправим в чат 1,5минутный отрывок
			example = soup.find('script', {'id': 'shoebox-media-api-cache-amp-music'}).text.replace('\\', '')
			example = re.findall('(https://audio-ssl.itunes.apple.com/[^"]+)', example)[index]
			example = requests.get(example, verify=False).content
			ex = 1
		except: select_track = ''
		# print(musician, album, select_track)

		#yandex
		ym_service = YMClient()
		search_result = ym_service.search(musician+album+select_track)
		if select_track!='':
			yalink = f"https://music.yandex.ru/track/{search_result['tracks']['results'][0]['id']}"
		elif album!='':
			yalink = f"https://music.yandex.ru/album/{search_result['albums']['results'][0]['id']}"
		else:
			yalink = f"https://music.yandex.ru/artist/{search_result['artists']['results'][0]['id']}"

		#spoty
		head = {
		'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
		'sec-ch-ua-mobile': '?0',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36'
		}
		resp = requests.get(f'https://open.spotify.com/search/{musician}{album}{select_track}', headers=head, verify=False).text
		soup = BeautifulSoup(resp, 'lxml')
		bearer = eval(soup.find('script').text.replace('true', 'True').replace('false','False').replace('null','None').strip())['accessToken']
		head = {'authorization':f'Bearer {bearer}'}
		resp = requests.get(f'https://api.spotify.com/v1/search?type=album%2Cartist%2Cplaylist%2Ctrack%2Cshow_audio%2Cepisode_audio&q={musician}+{album}+{select_track}&decorate_restrictions=false&best_match=true&include_external=audio&limit=10&market=RU', headers=head, verify=False).json()
		try:
			if select_track!='':
				spoty = resp['tracks']['items'][0]['external_urls']['spotify']
			elif album!='':
				spoty = resp['albums']['items'][0]['external_urls']['spotify']
			else:
				spoty = resp['artists']['items'][0]['external_urls']['spotify']
		except: spoty = ''

		while True:
			try:
				if spoty!='':
					bot.reply_to(message, f"<a href='{yalink}'>ссылка на Яндекс.Музыку\n</a><a href='{spoty}'>ссылка на Spotify</a>", parse_mode='html', disable_web_page_preview=True)
				else:
          #spotify хуже справляется с поиском
					bot.reply_to(message, f"<a href='{yalink}'>ссылка на Яндекс.Музыку</a>", parse_mode='html', disable_web_page_preview=True)
				if ex==1:
					bot.send_audio(message.chat.id, example)
				break
			except: pass

threading.Thread(target=bot.polling).start()