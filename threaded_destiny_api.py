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
	url = urlparse('https://www.bungie.net/Platform/' + urlext)
	conn = httplib.HTTPSConnection(url.netloc)
	conn.request('GET', url.path + "?" + url.query, headers={'X-Api-Key': 'f6736009a38a4707b549422b1bd69ea4'})
	res = conn.getresponse()
	data = res.read()
	conn.close()
	result = json.loads(data)
	return result
	
#single argument per list item when mapping
def getMembershipId(username):
	urlext = 'Destiny/SearchDestinyPlayer/2/' + username + '/'
	result = request(urlext)
	return result["Response"][0]["membershipId"]

#wrapper for getMembershipId that also returns the username label	
def getLabeledMembershipId(username):
	return (username, getMembershipId(username))

#single argument per list item when mapping
def getAccount(membershipId):
	urlext = 'Destiny/2/Account/' + membershipId + '/Summary/'
	result = request(urlext)
	return result

#single argument per list item when mapping
def getCharacterIds(membershipId):
	account = getAccount(membershipId)
	characters = account["Response"]["data"]["characters"]
	charIdList = [character["characterBase"]["characterId"] for character in characters]
	return charIdList

#single argument per list item when mapping	
def getClans(membershipId):
	urlext = 'User/GetBungieAccount/' + membershipId + '/2/'
	result = request(urlext)
	#if len(result["Response"]["relatedGroups"]) >  1:
	#	print "MULTIPLE RELATED GROUPS"
	#return [group for group in result["Response"]["relatedGroups"]]
	return [clan["groupId"] for clan in result["Response"]["clans"]]
	
#wrapper for getMemberClans that also returns the memId label
def getLabeledClans(membershipId):
	clans = getClans(membershipId)
	return (membershipId, clans)

def getClanId(clanName):
	urlext = 'Group/Name/'  + clanName + '/'
	result = request(urlext)
	return result["Response"]["detail"]["groupId"]

def getClanName(groupId):
	urlext = 'Group/' + groupId + '/'
	result = request(urlext)
	return result["Response"]["detail"]["name"]
	#result["Response"]["detail"]["clanCallsign"]

#wrapper for getClanName that also returns the groupId label
def getLabeledClanName(groupId):
	name = getClanName(groupId)
	return (groupId, name)
	
#get all memberIds for a clan with groupId, initial call does not need page
def getClanMembers(groupId, page=1):
	urlext = 'Group/' + groupId + '/ClanMembers/?platformType=2&currentPage=' + str(page)
	result = request(urlext)
	memberData = result["Response"]["results"]
	members = [member["destinyUserInfo"]["membershipId"] for member in memberData]
	if result["Response"]["hasMore"]:
		members.extend(getClanMembers(groupId, page+1))
	return members

def getLabeledClanMembers(groupId):
	members = getClanMembers(groupId)
	return (groupId, members)

#tuple of three arguments per list item when mapping
#args is (membershipId, characterId, mode)
def getCharacterActivity(args):
	membershipId, characterId, mode = args
	urlext = 'Destiny/Stats/ActivityHistory/2/' + membershipId + '/' + characterId + '/?mode=' + mode
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
	urlext = 'Destiny/Stats/PostGameCarnageReport/' + activityId + '/'
	result = request(urlext)
	players = result["Response"]["data"]["entries"]
	usernames = [entry["player"]["destinyUserInfo"]["displayName"] for entry in players]
	return usernames

#daemon worker thread function, calls targetFunc with argument from q
#writes result to outq
def worker(q, outq, targetFunc):
	while True:
		args = q.get()
		if not args: #args is None (sentinel)
			return #shutdown thread
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

