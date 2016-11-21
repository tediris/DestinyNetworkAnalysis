import json
from collections import defaultdict

from threading import Thread
from Queue import Queue
import httplib, sys
from urlparse import urlparse, parse_qs
from urllib import urlencode

#utility function for an HTTPS GET request to Bungie API with extension urlext
#reads response body as json
def request(urlext):
	url = urlparse('https://www.bungie.net/Platform/Destiny/' + urlext)
	#url_qs = urlencode(parse_qs(url.query[:-1]), True)
	conn = httplib.HTTPSConnection(url.netloc)
	conn.request('GET', url.path + "?" + url.query, headers={'X-Api-Key': 'f6736009a38a4707b549422b1bd69ea4'})
	res = conn.getresponse()
	data = res.read()
	conn.close()
	result = json.loads(data)
	return result
	
#single argument per list item when mapping
def getMembershipId(username):
	urlext = 'SearchDestinyPlayer/2/' + username + '/'
	result = request(urlext)
	return result["Response"][0]["membershipId"]

#single argument per list item when mapping
def getCharacterIds(membershipId):
	urlext = '2/Account/' + membershipId + '/'
	result = request(urlext)
	characters = result["Response"]["data"]["characters"]
	charIdList = [character["characterBase"]["characterId"] for character in characters]
	return charIdList

#tuple of three arguments per list item when mapping
#args is (membershipId, characterId, mode)
def getCharacterActivity(args):
	membershipId, characterId, mode = args
	urlext = 'Stats/ActivityHistory/2/' + membershipId + '/' + characterId + '/?mode=' + mode
	result = request(urlext)
	if "activities" not in result["Response"]["data"]:
	    print "Could not find activities"
	    print result["Response"]
	    print result["Response"]["data"]
	    return []
	activities = result["Response"]["data"]["activities"]
	activityIds = [activity["activityDetails"]["instanceId"] for activity in activities]
	return activityIds

#single argument per list item when mapping
def getActivityUsernames(activityId):
	urlext = 'Stats/PostGameCarnageReport/' + activityId + '/'
	result = request(urlext)
	players = result["Response"]["data"]["entries"]
	usernames = [entry["player"]["destinyUserInfo"]["displayName"] for entry in players]
	return usernames

#daemon worker thread function, calls targetFunc with argument from q
#writes result to outq
def worker(q, outq, targetFunc):
	while True:
		args = q.get()
		result = targetFunc(args)
		outq.put(result)
		print "recorded response"
		q.task_done()

#maps a targetFunc called with args from argslist to nthreads
#blocks until done and returns outq with results
def mapFns(targetFunc, argslist, nthreads):
	print "mapping"
	q = Queue(nthreads*2)
	outq = Queue()
	for i in range(nthreads):
		t = Thread(target=worker, args=[q, outq, targetFunc])
		t.daemon = True
		t.start()
	try:
		for args in argslist:
			q.put(args)
		q.join()
	except KeyboardInterrupt:
		sys.exit(1)
	return outq

#finds players for past 'limit' # of activities of type 'mode' for provided character
#returns a dictionary of player names to # of times played together
def getRecentPlayerMap(membershipId, characterId, mode='None', limit=25, nthreads=25):
	activityIds = getCharacterActivity((membershipId, characterId, mode))
	activityIds = activityIds[:min(limit, len(activityIds))]
	outq = mapFns(getActivityUsernames, activityIds, nthreads)
	
	#count players
	outq.put(None)
	counts = defaultdict(int)
	for result in iter(outq.get, None):
		for player in result:
			counts[player] += 1
	return counts
	
#wrapper for getRecentPlayerMap - removes self from result and orders by count
def getActivityMembers(username, mode='None', limit=25, nthreads=25):
	membershipId = getMembershipId(username)
	characterIds = getCharacterIds(membershipId)
	recentPlayers = getRecentPlayerMap(membershipId, characterIds[0], mode, limit, nthreads)
	result = []
	for membername, count in recentPlayers.iteritems():
		if membername != username:
			result.append((str(membername), count))
	return sorted(result, key=lambda x: x[1], reverse=True)
