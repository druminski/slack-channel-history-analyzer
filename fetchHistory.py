import urllib2, json, time, argparse

parser = argparse.ArgumentParser(description='Fetch history of specified Slack channel.')

parser.add_argument('--channel', '-channel', required=True, help='Slack channel ID. Required.')
parser.add_argument('--token', '-token', required=True, help='Token allowing to fetch Slack channel history. Required.')
parser.add_argument('--output', '-output', default='history.json', help='Output file name to which save Slack history (default: %(default)s).')

args = parser.parse_args()

channel = args.channel
token = args.token
output = args.output

hasMore = True
cursor = ""
mergedJson = {
  'messages': []
}
page = 0

def fetchMessages(url):
  request = urllib2.Request(url)
  request.add_header("Authorization", "Bearer " + token)
  response = urllib2.urlopen(request)

  return json.loads(response.read())

print('Fetching main thread')

while hasMore:
  url = 'https://slack.com/api/conversations.history?channel={}&pretty=1'.format(channel)
  if cursor:
    url = url + '&cursor=' + cursor 

  j = fetchMessages(url)

  if j['ok']:
    print('Fetched page {} with cursor {}'.format(page, cursor))
    mergedJson['messages'] += j['messages']
    hasMore = j['has_more']
    if hasMore:
      cursor = j['response_metadata']['next_cursor']
  else:
    print('Error while fetching page {} with cursor {} and url {}'.format(page, cursor, url))

  page += 1

mainMessages = mergedJson['messages']

allMessages = []
i = 0

print('Finished fetching main thread. Fetching replies:')

for m in mainMessages:
  ts = mainMessages[i]['ts']
  cursor = ''
  hasMore = True
  page = 0
  while hasMore:
    url = 'https://slack.com/api/conversations.replies?channel={}&pretty=1&ts={}'.format(channel, ts)
    if cursor:
      url = url + '&cursor=' + cursor
    j = fetchMessages(url)
  
    if j['ok']:
      print('Fetched thread with ts: {}; Iteration: {}; Page {}; Cursor: {}'.format(ts, i, page, cursor))
      allMessages += j['messages']
      hasMore = j['has_more']
      page += 1
      if hasMore:
        cursor = j['response_metadata']['next_cursor']
    else:
      print('Error while fetched page {} with cursor {} and url {}'.format(page, cursor, url))

  i += 1
  if i % 100 == 0:
    print('Sleeping for 60 seconds due to rate limit on Slack server side')
    time.sleep(60)


f = open(output, "w")
f.write(json.dumps(allMessages, indent=4, sort_keys=False))
f.close()

print('Successfully fetched channel history and saved into \'{}\' file'.format(output))
