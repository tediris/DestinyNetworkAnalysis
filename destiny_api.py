import requests
import grequests
import json
import pprint
from multiprocessing.pool import ThreadPool
#from pathos.multiprocessing import ProcessPool
from collections import defaultdict

class DestinyAPI:
	def __init__(self, apiKey, numThreads=10):
		# self.threadPool = ThreadPool(numThreads)
		self.apiKey = apiKey
		self.headers = {'X-Api-Key': apiKey}
		self.apiBase = 'https://www.bungie.net/Platform/Destiny/'

	def getMembershipId(self, username):
		url = self.apiBase + 'SearchDestinyPlayer/2/' + username
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		return result["Response"][0]["membershipId"]
		
	def getBungieAccount(self, membershipId):
		url = 'https://www.bungie.net/Platform/User/GetBungieAccount/' + membershipId + '/2/'
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		return result["Response"]
		
	def getClanInfo(self, groupId):
		url = 'https://www.bungie.net/Platform/Group/' + groupId
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		return result["Response"]
		
	def getClansForUser(self, username):
		memId = self.getMembershipId(username)
		account = self.getBungieAccount(memId)
		clanIds = [clan["groupId"] for clan in account["clans"]]
		clanNames = []
		for clanId in clanIds:
			clanInfo = self.getClanInfo(clanId)
			clanNames.append(self.getClanInfo(clanId)["detail"]["name"])
		return clanNames
		
	def getCharacterIds(self, membershipId):
		url = self.apiBase + '2/Account/' + membershipId
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		characters = result["Response"]["data"]["characters"]
		charIdList = [character["characterBase"]["characterId"] for character in characters]
		return charIdList

	def getCharacterActivity(self, membershipId, characterId, mode='None'):
		url = self.apiBase + 'Stats/ActivityHistory/2/' + membershipId + '/' + characterId + '/?mode=' + mode
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		if "activities" not in result["Response"]["data"]:
		    print "Could not find activities"
		    print result["Response"]
		    print result["Response"]["data"]
		    return []
		activities = result["Response"]["data"]["activities"]
		activityIds = [activity["activityDetails"]["instanceId"] for activity in activities]
		return activityIds

	def getPlayersInActivity(self, activityId):
		url = self.apiBase + 'Stats/PostGameCarnageReport/' + activityId
		r = requests.get(url, headers=self.headers)
		result = json.loads(r.content)
		players = result["Response"]["data"]["entries"]
		usernames = [entry["player"]["destinyUserInfo"]["displayName"] for entry in players]
		return usernames

	def getRecentPlayerMap(self, membershipID, characterId, mode='None'):
		activityIds = self.getCharacterActivity(membershipID, characterId, mode)
		pool = ThreadPool(16)
		#pool = ProcessPool(8)
		results = pool.map(self.getPlayersInActivity, activityIds)
		pool.close()
		pool.join()
		mapping = defaultdict(int)
		for result in results:
			for player in result:
				mapping[player] += 1
		return mapping
		
	#grequests multithreading requests version
	def getRecentPlayerMap2(self, membershipID, characterId, mode='None'):
		activityIds = self.getCharacterActivity(membershipID, characterId, mode)
		activityIds = activityIds[:min(10,len(activityIds))] #limit to 10 most recent activities
		urlHeads = [(self.apiBase + 'Stats/PostGameCarnageReport/' + activityId, self.headers) for activityId in activityIds]
		print "mapping"
		rqs = [grequests.get(urlHead[0], headers=urlHead[1]) for urlHead in urlHeads]
		rs = grequests.imap(rqs) #imap returns iterator, runs faster
		results = []
		print "processing returned info"
		for r in rs:
			result = json.loads(r.content)
			players = result["Response"]["data"]["entries"]
			usernames = [entry["player"]["destinyUserInfo"]["displayName"] for entry in players]
			results.append(usernames)
		
		#count players
		mapping = defaultdict(int)
		for result in results:
			for player in result:
				mapping[player] += 1
		return mapping
		
	def getRaidMembers(self, username):
		memId = self.getMembershipId(username)
		charIds = self.getCharacterIds(memId)
		recentPlayers = self.getRecentPlayerMap(memId, charIds[0], 'Raid')
		result = []
		for key, value in recentPlayers.iteritems():
			if key != username:
				result.append((str(key), value))
		return sorted(result, key=lambda x: x[1], reverse=True)

	#generic version
	def getActivityMembers(self, username, mode):
		memId = self.getMembershipId(username)
		charIds = self.getCharacterIds(memId)
		recentPlayers = self.getRecentPlayerMap2(memId, charIds[0], mode)
		result = []
		for key, value in recentPlayers.iteritems():
			if key != username:
				result.append((str(key), value))
		return sorted(result, key=lambda x: x[1], reverse=True)
		

def test_basic():
	api = DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
	memId = api.getMembershipId('neoleopard')
	charIds = api.getCharacterIds(memId)
	activityIds = api.getCharacterActivity(memId, charIds[0])
	# print api.getPlayersInActivity(activityIds[0])
	print api.getRecentPlayerMap(memId, charIds[0])

def test_2():
	api = DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
	print api.getClansForUser('neoleopard')

# api = DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
# print api.getRaidMembers('neoleopard')
# test_2()
