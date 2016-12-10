import snap
import numpy as np
import dill
import threaded_destiny_api as da
from collections import defaultdict

mode = 'Raid'

#load graph and name-to-node/node-to-name mapping dicts
FIn = snap.TFIn(mode+"Graph.graph")
graph = snap.TUNGraph.Load(FIn)
nodeMapping, nameMapping = dill.load(open(mode+"Mappings.pkl", 'r'))

#basic info
snap.PrintInfo(graph, mode + " Graph")

edgeBridges = snap.TIntPrV()
snap.GetEdgeBridges(graph, edgeBridges)
print "Number of edge bridges is %d" %len(edgeBridges)
print "Clustering Coefficient: %f" %snap.GetClustCf(graph)
print "Triads: %d" %snap.GetTriads(graph)
DegToCntV = snap.TIntPrV()
snap.GetDegCnt(graph, DegToCntV)
nodesum = 0
for item in DegToCntV:
	print "%d nodes with degree %d" %(item.GetVal2(), item.GetVal1())
	nodesum += item.GetVal2()*item.GetVal1()
print "average node degree is: %f" %(float(nodesum)/graph.GetNodes())
	
#clustering
print "Communities:"
CmtyV = snap.TCnComV()
modularity = snap.CommunityCNM(graph, CmtyV)
print len(CmtyV)
print "The modularity of the network is %f" %modularity

#clan analysis:
memIdMapping = {}
names = nodeMapping.keys()
outq = da.mapFns(da.getLabeledMembershipId, names, 25)
outq.put(None)

for name, memId in iter(outq.get, None):
	memIdMapping[memId] = name

memIds = [memId for memId in memIdMapping]
outq = da.mapFns(da.getLabeledClans, memIds, 25)
outq.put(None)

clanIds = []
groupMapping = {}
for memId, groupIds in iter(outq.get, None):
	if groupIds:
		clanIds.append(groupIds[0])
		groupMapping[memId] = groupIds[0]
	else:
		groupMapping[memId] = None

outq = da.mapFns(da.getLabeledClanName, clanIds, 25)
outq.put(None)

clans = defaultdict(int)
hadClans = 0
groupNameMapping = {}
for groupId, name in iter(outq.get, None):
	clans[name] += 1
	hadClans += 1
	groupNameMapping[groupId] = name
	
print clans
print len(clans)
print hadClans
with open(mode + "Clans.pkl", 'w') as f:
	dill.dump((clans, groupMapping, groupNameMapping), f)
	
unknownClan = [memId for memId in groupMapping if groupMapping[memId] == None]
print unknownClan
groupMemberMapping = {}
outq = da.mapFns(da.getLabeledClanMembers, clanIds, 25)
outq.put(None)

for groupId, members in iter(outq.get, None):
	groupMemberMapping[groupId] = set(members)

for unknownClanMember in unknownClan:
	print "Matching unknown clan player " + memIdMapping[unknownClanMember] + " to known clans"
	for groupId in groupMemberMapping:
		if unknownClanMember in groupMemberMapping[groupId]:
			groupMapping[unknownClanMember] = groupId
			print "Mapped unknown player " + memIdMapping[unknownClanMember] + " to " + groupNameMapping[groupId]
			clans[groupNameMapping[groupId]] += 1
			hadClans += 1
			continue
print clans
print len(clans)
print hadClans

	



'''
print "collecting clans"
allclans = {}
api = da.DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
names = [nameMapping[nodeI.GetId()] for nodeI in graph.Nodes()]
print len(names)
clans = api.getClansForUsers(names)
print len(clans)
for index in range(len(names)):
	clan = clans[index]
	if not clan:
		continue
	if clan not in allclans:
		allclans[clan] = set([])
	allclans[clan].add(nodeMapping[names[index]])
#print len(allclans)
#with open(mode + "Clans.pkl", 'w') as f:
#	dill.dump(allclans, f)
	
'''

		
	
	
	
	
	
