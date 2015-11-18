import networkx as nx
import re

__author__ = 'Rob'


def largest_component(components):
    largest = set()
    length = 0
    for comp in components:
        if len(comp) > length:
            length = len(comp)
            print(largest, ' => ', comp)
            largest = comp
        else:
            print(comp, ' < ', largest)
    return largest

def split(inn, path1, path2):
    out1 = open(path1, 'w')
    out2 = open(path2, 'w')
    with open(inn, "r") as ins:
        for line in ins:
            if line[0] == ' ':
                break
            out2.write(line)
        for line in ins:
            out1.write(line[1:])
    out1.close()
    out2.close()

G = nx.DiGraph()
#split("utwente20151116.dot", "edges.dot", "urls.dot")
d = dict()
with open("edges.dot", "r") as ins:
    for line in ins:
        nodes = re.split('-> {', line)
        edges = re.findall('\d+', nodes[1])
        for edge in edges:
            if edge not in d:
                d[edge] = 1
            else:
                d[edge] += 1
matches = dict()
with open("urls.dot", "r") as ins:
    for line in ins:
        splitted = line.split(" ")
        matches[splitted[0]] = splitted[1].split("\"")[1]
items = sorted(d.items(), key=lambda x:x[1], reverse=True)

pairs = [(number, matches[index]) for (index,number) in items if index in matches]

out = open("result.txt", 'w')
for pair in pairs:
    out.write(str(pair[0])),
    out.write(" : "),
    out.write(str(pair[1]))
    out.write("\n")
print("done")
out.close()