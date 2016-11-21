#import destiny_api as da
import threaded_destiny_api as da
import snap
import numpy as np
import dill

#file globals
origin = 'neoleopard'
nodeMapping = {origin:0} #names to nodeIds
nameMapping = {0:origin} #nodeIds to names
nextNodeNum = 1 #origin player is 0

def crawl(graph, player, searched, depth, mode):
    global nodeMapping
    global nameMapping
    global nextNodeNum
    if depth==0:
        return
        
    #api = da.DestinyAPI('f6736009a38a4707b549422b1bd69ea4')
    #activityMembers = api.getActivityMembers(player, mode)
    activityMembers = da.getActivityMembers(player, mode, 25, 25)
    searched.add(player) #mark player as visited
    
    #add to graph
    names = []
    weights = []
    for memberName, weight in activityMembers:
        if memberName not in nodeMapping:
            #record new node
            nodeMapping[memberName] = nextNodeNum
            nameMapping[nextNodeNum] = memberName
            graph.AddNode(nextNodeNum)
            nextNodeNum += 1
        if memberName not in searched:
            #consider as potential next search point
            names.append(memberName)
            weights.append(weight)
        graph.AddEdge(nodeMapping[player], nodeMapping[memberName])

    #cut recursion if all neighbors searched
    if not names:
        return

    #normalize weights as probabilities
    weights = np.asarray(weights, dtype=np.float)
    weights /= weights.sum()

    #search up to 3 sampled neighbors (weighted by edge weights)
    nextSearches = np.random.choice(names, size=min(3,len(names)), replace=False, p=weights)
    for name in nextSearches:
        crawl(graph, name, searched, depth-1, mode)



def buildGraph(mode):
    global nodeMapping
    global nameMapping
    graph = snap.TUNGraph.New()
    graph.AddNode(0)    
    #collect graph (recursion depth 5)
    crawl(graph, origin, set([]), 5, mode)
    #remove nodes of degree 1
    snap.DelDegKNodes(graph, 1, 1)
    snap.PrintInfo(graph, "Destiny " + mode + " Network")
    #save graph
    FOut = snap.TFOut(mode + "Graph.graph")
    graph.Save(FOut)
    FOut.Flush()
    #save dicts
    with open(mode + "Mappings.pkl", 'w') as f:
        dill.dump((nodeMapping, nameMapping), f)
    #attempt to draw graph
    snap.DrawGViz(graph, snap.gvlNeato, mode + "Graph.png", mode + " Graph", True)
    
    
buildGraph('Raid')

