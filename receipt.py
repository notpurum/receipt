# -*- coding: utf-8 -*-


import requests
import pprint
import re
import time
import random
from adjustments import adjustments

class Receipt:
	def __init__(self, phone=None, password=None):
		self.url = 'https://proverkacheka.nalog.ru:9999/v1'
		self.phone = phone
		self.password = password
		self.login_data = (phone, password)

	def registration(self, email, name, phone):
		reg = {"email": email,   # mail@mail.ru
			   "name": name,     # Ivan Pupkin
			   "phone": phone}   # +79171234567
		r = requests.post(self.url + '/mobile/users/signup', json=reg)
		return r.text

	def login(self, phone, password):
		self.phone = phone
		self.password = password
		self.login_data = (phone, password)
		r = requests.get(self.url + '/mobile/users/login', auth=self.login_data)
		return r.text

	def restore_password(self, phone):
		restore = {"phone": phone} # +79171234567
		r = requests.post(self.url + '/mobile/users/restore', json=restore)
		return r.text
	
	def receipt_exist(self, check):
		# FN, type, FD, FPD, date, sum
		check_url = self.url + '/ofds/*/inns/*/fss/{}/operations/{}/tickets/{}?fiscalSign={}&date={}&sum={}'
		r = requests.get(check_url.format(check['fn'],
										check['n'],
										check['i'],
										check['fp'],
										check['t'],
										check['s']),
										auth=self.login_data)
		# print(r)
		# print(r.status_code)
		# print(r.text)
		return 

	def receipt_info(self, check):
		# Needs to be checked. Doesn't work else.
		self.receipt_exist(check)

		headers = {
			'User-Agent': 'okhttp/3.0.1',
			'Device-Id': '748036d688ec41c6',
			'Device-OS': 'Windows',
			'Version': '2',
			'ClientVersion': '1.4.4.1',
			'Host': 'proverkacheka.nalog.ru:9999',
			'Connection': 'proverkacheka.nalog.ru:9999'
			}

		# FN, FD, FPD	
		url = 'https://proverkacheka.nalog.ru:9999/v1/inns/*/kkts/*/fss/{}/tickets/{}?fiscalSign={}&sendToEmail=no'
		status_code = 0
		while not status_code == 200:
			r = requests.get(url.format(check['fn'],
										check['i'],
										check['fp']),
										headers=headers,
										auth=self.login_data)
			status_code = r.status_code
			# print(status_code, end=' ')
			if not status_code == 200:
				print(r.text)
			else:
				print()
			time.sleep(1)
		check_json = r.json()
		# pprint.pprint(check_json)
		self.check_json = check_json
		return self.check_json
		
	def _get_items_from_check(self, check_json):
		return check_json['document']['receipt']['items']

	def _get_data_from_check(self, check_json):
		return check_json['document']['receipt']['dateTime']

	def _sub(self, pattern, new_name, old_name):
		return re.sub(pattern, new_name, old_name, flags=re.IGNORECASE)

	def _parse_check(self, items):
		#### Extracting usefull info
		token_name             = re.compile('((?:[А-Я][а-я]+)(?:\s[а-я]+)*)') # Паттерн для извлечения имён из нормальных строк
		token_name_ignorecase  = re.compile('([А-Яа-яЁё]+)+')                 # Для корявых строк
		token_quantity         = re.compile('\W?(\d+)\s?(?=(?:(?:шт|мл|кг|гр?|л)(?:$|[^а-яА-ЯеЁ])))') # Количество
		token_measure          = re.compile('((?<=\d)\s?(?:(?:шт|мл|кг|гр?|л)(?:$|[^а-яА-ЯеЁ])))')    # Единицы измерения

		filtered_items = []
		for item in items:
			# Извлекаем вид товара (молоко, хлеб, масло, чипсы)
			try:
				name = token_name.findall(item['name'])[0].strip().lower()
			except:
				name = token_name_ignorecase.findall(item['name'])[0].strip().lower()
			if name == 'доставка':
				continue
			# Заменяем плохие названия на нормальные (Пив —> Пиво)
			for adjustment in adjustments:
				name = self._sub(adjustment, adjustments[adjustment], name).lower()
			# print(item['name'])

			# Извлекаем количество и меру весов, если есть
			try:
				# print('Ищем вес')
				quantity_int = int(token_quantity.findall(item['name'].lower())[0])
				quantity_measure = token_measure.findall(item['name'].lower())[0].strip(',').strip('.').strip().lower()
				# В названии пакета может быть его выдерживаемый вес. Заменяем на шт.
				if re.findall('(^пакет$)', name.lower()) or\
				   re.findall('(^пакеты$)', name.lower()) or\
				   re.findall('(^мешок$)', name.lower()) or\
				   re.findall('(^мешки$)', name.lower()):
					quantity_int = 1
					quantity_measure = 'шт'
			except:
				# print('Вес не обнаружен')
				quantity_int = 1
				if float(item['quantity']).is_integer():
					quantity_measure = 'шт'
				else:
					quantity_measure = 'кг'

			total = item['sum']
			price = item['price']
			quantity_exact = round(float(item['quantity']), 2)

			if quantity_measure == 'л' or quantity_measure == 'кг' or quantity_measure == 'шт':
				price_per_volume = int(price / quantity_int)
				per_volume_measure = quantity_measure
			elif quantity_measure == 'мл':
				price_per_volume = int(price / (quantity_int) * 1000)
				per_volume_measure = 'л'
			elif quantity_measure == 'г':
				price_per_volume = int(price / (quantity_int) * 1000)
				per_volume_measure = 'кг'

			price_per_volume = round(price_per_volume, 2)

			# print(name + ',', end=' '),
			# print(quantity_int * quantity_exact, quantity_measure + ',', end=' ')
			# print(price_per_volume, '₽ за', per_volume_measure + ',', end=' ')
			# print('сумма', total, '₽')

			date = self._get_data_from_check(self.check_json)

			filtered_items.append({
			'receipt_details': self.receipt_details,
			'date_time': date,
			'raw_text': item['name'],
			'raw_quantity': item['quantity'],
			'raw_price': item['price'],
			'raw_total': item['sum'],
			'filtered_name': name,
			'filtered_quantity': quantity_int,
			'filtered_quantity_measure': quantity_measure,
			'filtered_price_per_volume': price_per_volume,
			'filtered_price_per_volume_measure': per_volume_measure
			})
		return filtered_items


	def _create_check(self, text):
		self.receipt_details = text
		check = {}
		for pair in text.split('&'):
			check[pair.split('=')[0]] = pair.split('=')[1]
		return check

	def process_check(self, text):
		check = self._create_check(text)
		receipt = self.receipt_info(check)
		items = self._get_items_from_check(receipt)
		return self._parse_check(items)
