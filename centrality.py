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

# get centrality measures
eigenCentrality = snap.TIntFltH()
snap.GetEigenVectorCentr(graph, eigenCentrality)

nodeBetweenessCentrality = snap.TIntFltH()
Edges = snap.TIntPrFltH()

snap.GetBetweennessCentr(graph, nodeBetweenessCentrality, Edges, 1.0)

for node in eigenCentrality:
    degreeCentrality = snap.GetDegreeCentr(graph, node)
    print "node: %d, centr: %f, %f, %f" % (node, degreeCentrality, nodeBetweenessCentrality[node], eigenCentrality[node])
