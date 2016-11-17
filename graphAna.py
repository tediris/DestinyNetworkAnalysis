import snap
import numpy as np
import dill

#load graph and name-to-node/node-to-name mapping dicts
FIn = snap.TFIn("raidgraph.graph")
graph = snap.TUNGraph.Load(FIn)
nodeMapping, nameMapping = dill.load(open('mappings.pkl', 'r'))

#basic info
snap.PrintInfo(graph, "raid graph")
edgeBridges = snap.TIntPrV()
snap.GetEdgeBridges(graph, edgeBridges)
print "Number of edge bridges is %d" %len(edgeBridges)
print "Clustering Coefficient: %f" %snap.GetClustCf(graph)
print "Triads: %d" %snap.GetTriads(graph)
DegToCntV = snap.TIntPrV()
snap.GetDegCnt(graph, DegToCntV)
for item in DegToCntV:
    print "%d nodes with degree %d" %(item.GetVal2(), item.GetVal1())

#clustering
print "Communities:"
CmtyV = snap.TCnComV()
modularity = snap.CommunityCNM(graph, CmtyV)
print len(CmtyV)
for Cmty in CmtyV:
    print "Community"
    print len(Cmty)
    for nid in Cmty:
        print nameMapping[nid]
print "The modularity of the network is %f" %modularity
