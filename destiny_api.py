import requests
import json
from multiprocessing.pool import ThreadPool
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

	def getRecentPlayerMap(self, membershipID, characterId):
		activityIds = self.getCharacterActivity(membershipID, characterId, 'Raid')
		pool = ThreadPool(16)
		results = pool.map(self.getPlayersInActivity, activityIds)
		pool.close()
		pool.join()
		mapping = defaultdict(int)
		for result in results:
			for player in result:
				mapping[player] += 1
		return mapping

	def getRaidMembers(self, username):
		memId = self.getMembershipId(username)
		charIds = self.getCharacterIds(memId)
		recentPlayers = self.getRecentPlayerMap(memId, charIds[0])
		result = []
		for key, value in recentPlayers.iteritems():
			if key != username:
				result.append((key, value))
		return sorted(result, key=lambda x: x[1], reverse=True)


def test_basic():
	api = DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
	memId = api.getMembershipId('neoleopard')
	charIds = api.getCharacterIds(memId)
	activityIds = api.getCharacterActivity(memId, charIds[0])
	# print api.getPlayersInActivity(activityIds[0])
	print api.getRecentPlayerMap(memId, charIds[0])

api = DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
print api.getRaidMembers('neoleopard')
