"""
traverse a json file with subclass relations and print out the transitive closure of
transitive subclass relationships
"""

import json


def process(branch):
    """compute the distance for a branch for all nodes up to the leaf and
    recurse towards the root"""

    # the branch contains the leaves on the right.
    # As we progress towards the root, we add nodes to the left
    ego = branch[0]
    if ego == "novalue":  # wpdata does not use None
        return
    # store all descendents with distance
    for i, descendent in enumerate(branch):
        storeline = (ego, i, descendent)
        store[(storeline)] = True
    # recurse for all parents
    parents = tree[ego]["p279s"]
    if parents is None:
        return
    for parent in parents:
        if parent:
            if parent in knownloops:
                continue
            if parent in branch:
                print("loop detected", parent)
            # prepend the ancestor and push back the list of descendents
            process([parent] + branch)


if __name__ == "__main__":
    # function, graph, multigraph loop back to themselves in their line of descendency.
    knownloops = ["Q141488", "Q11348", "Q2642629"]
    # read the input file
    tree = json.loads(open("superclasses.json").read())
    # prepare collection of csv lines
    store = {}
    # traverse input file
    for leaf in tree:
        process([leaf])
    # write output
    with open("closure.csv", "w") as out:
        for line in sorted(store.keys()):
            if line[1] > 0:
                out.write("%s\t%s\t%s\n" % line)
