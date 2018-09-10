from requests import get
from requests.exceptions import RequestException
from contextlib import closing
from bs4 import BeautifulSoup
import re
import json
import sys

def simple_get(url):
  try:
    with closing(get(url, stream=True)) as resp:
      if is_good_response(resp):
        return resp.content
      else:
        return None
  
  except RequestException as e:
      log_error('Error during requests to {0} : {1}'.format(url, str(e)))
      return None

def is_good_response(resp):
  content_type = resp.headers['Content-Type'].lower()
  return (resp.status_code == 200
          and content_type is not None
          and content_type.find('html') > -1)

def log_error(e):
  print(e)

def parse_events(count, count2, event_temp, date_temp, raw_html):
  html = BeautifulSoup(raw_html, 'html.parser')
  events = html.find_all('a', href=re.compile(
      "https://officenters.com/event/"))

  for event in events:
    if (event.string != '[Read More...]' and event.string != None and event.string != '(See all)'):
      print('{0}. {1}'.format(count, event.string.strip()))
      event_temp[count] = event.string.strip()
      count += 1

  dates = html.find_all('span', class_=re.compile("tribe-event-date-start"))
  
  for date in dates:
    print('{0}. {1}'.format(count2, date.string.strip()))
    date_temp[count2] = date.string.strip()
    count2 += 1
  
  if (count != count2):
    sys.exit("DATE / EVENT COUNT UNMATCHED")

  return count, count2, event_temp, date_temp

def retrieve_events(event_temp, date_temp, event_storage):
  count = 1
  count2 = 1
  raw_html = simple_get('https://officenters.com/events/')
  count, count2, event_temp, date_temp = parse_events(count, count2, event_temp, date_temp, raw_html)
  i = 2
  prev_count = 0
  while (prev_count != count):
    prev_count = count
    raw_html = simple_get(
        'http://officenters.com/events/?action=tribe_photo&tribe_paged=' + str(i) + '&tribe_event_display=photo')
    count, count2, event_temp, date_temp = parse_events(count, count2, event_temp, date_temp, raw_html)
    i += 1

  for x in range(1, count):
    event_storage[date_temp[x]] = event_temp[x]

  print("Retrieved All Events.")
  return event_storage

def save_event_data(event_storage):
  event_json = json.dumps(event_storage)
  with open('events.json', 'w') as outfile:
    json.dump(event_json, outfile)

def load_saved_data():
  with open('events.json', 'r') as data_file:
    saved_events = json.loads(data_file.read())
  return saved_events

def write_files(event_storage, previous_events):
  f_current = open("current_events.txt", "w")
  f_previous = open("previous_events.txt", "w")

  for x, y in event_storage.items():
    f_current.write('{0} {1}\n'.format(x, y))
  for x, y in previous_events.items():
    f_previous.write('{0} {1}\n'.format(x, y))

  f_current.close()
  f_previous.close()



def main():
  event_temp = {}
  date_temp = {}
  event_storage = {}
  event_storage = retrieve_events(event_temp, date_temp, event_storage)
  previous_events = {}
  previous_events = json.loads(load_saved_data())

  write_files(event_storage, previous_events)

  while(True):
    option = input('Save data as current events? y for yes, n for no: ')
    if(option == 'y'):
      save_event_data(event_storage)
      print('Event data saved.')
      break
    elif(option == 'n'):
      print("Data not saved.")
      break
    else:
      print('Not a valid option')
  

main()
