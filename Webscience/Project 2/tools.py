import networkx as nx
import re as re

seperator, newline, divider = '-----', '\n', '/'

def load_graph(location, treshold):

    graph = nx.DiGraph()
    with open(location, 'r') as file:
        for line in file:
            connections = re.split(' -> {', line)
            if connections:
                node = re.findall('\d+', connections[0])
                if len(node) == 1:
                    predecessors = re.findall('\d+', connections[1])
                    if len(predecessors) > treshold:
                        for elem in predecessors:
                            graph.add_edge(node[0], elem)
    return graph


def write_results(location, pr, inc, outc, tenc, tubec, disc):
    with open(location, 'w') as file:
        file.write('Pagerank: ' + str(pr) + newline)
        file.write(seperator + newline)
        file.write('In: ' + str(inc) + newline)
        file.write(seperator + newline)
        file.write('Out: ' + str(outc) + newline)
        file.write(seperator + newline)
        file.write('Tendrils: ' + str(tenc) + newline)
        file.write(seperator + newline)
        file.write('Tubes: ' + str(tubec) + newline)
        file.write(seperator + newline)
        file.write('Disconnected: ' + str(disc) + newline)

def print_process(text, current, total, interval):
    if interval > 0:
        if current % interval == 0:
            print(text, current, divider, total)