from _hashlib import new
import os.path
import networkx as nx
import re
import time

separator, newline, divider = '-----', '\n', '/'


# Splits the initial .dot file to a url-file and an edges file, usable by the second trimming method
def split_dot_file(in_loc, urls_out, edges_out):
    with open(in_loc, 'r') as in_file:
        # parse urls
        urls_file = open(urls_out, 'w')
        line = in_file.readline()
        urls = {}
        while line:
            connections = re.split(' \[url=\\"', line)
            if len(connections) == 2:
                urls_file.write(connections[0] + ";" + connections[1][:-4] + newline)
                urls[connections[0]] = connections[1][:-4]
            line = in_file.readline()
            if line[0] == ' ':
                break
        urls_file.close()
        # sort edges to number of slashes
        edges = []
        leftovers = []
        while line:
            parts = re.split(' -> {', line[1:])
            if parts[0] in urls:
                edges.append((urls[parts[0]], parts))
            else:
                leftovers.append(parts)
            line = in_file.readline();
            if line[0] != ' ':
                break
        edges = sorted(edges, key=lambda x: x[0].count("/"), reverse=True)
        # write edges
        edges_file = open(edges_out, 'w')
        for edge in edges:
            edges_file.write(edge[1][0] + ' -> {' + edge[1][1])
        for leftover in leftovers:
            edges_file.write(leftover[0] + ' -> {' + leftover[1])
        edges_file.close()


# Splits the initial .dot file to a url-file and an edges file, usable by the first trimming method
def split_dot_file_old(in_loc, urls_out, edges_out):
    with open(in_loc, 'r') as in_file:
        # parse urls
        urls_file = open(urls_out, 'w')
        line = in_file.readline()
        while line:
            connections = re.split(' \[url=\\"', line)
            if len(connections) == 2:
                urls_file.write(connections[0] + ";" + connections[1][:-4] + newline)
            line = in_file.readline()
            if line[0] == ' ':
                break
        urls_file.close()
        # parse edges
        edges_file = open(urls_out, 'w')
        while line:
            edges_file.write(line[1:])
            line = in_file.readline()
            if line[0] != ' ':
                break
        edges_file.close()

# calculates the in-degrees from the input file and writes it to the output file
def calculate_indegrees(in_loc, out_loc):
    indegrees = {}
    with open(in_loc, 'r') as in_file:
        for line in in_file:
            connections = re.split(' -> {', line)
            if connections:
                ancestors = re.findall('\d+', connections[1])
                for ancestor in ancestors:
                    if ancestor not in indegrees:
                        indegrees[ancestor] = 1
                    else:
                        indegrees[ancestor] += 1
    out_file = open(out_loc, 'w')
    out_file.write("Node id; In degrees" + newline)
    listt = sorted(indegrees.items(), key=lambda x: x[1], reverse=False)
    for item in listt:
        out_file.write(str(item[0]) + "; " + str(item[1]) + newline)
    out_file.close()

# loads the graph using the second trim method
def load_graph(location, treshold):
    graph = nx.DiGraph()
    with open(location, 'r') as file:
        cntr = 0
        for line in file:
            connections = re.split(' -> {', line)
            if connections:
                predecessors = re.findall('\d+', connections[1])
                for elem in predecessors:
                    graph.add_edge(connections[0], elem)
                if nx.number_of_nodes(graph) >= treshold:
                    return graph
            cntr += 1
    return graph


# loads the graph using the first trim method
def load_graph_old(location, treshold):
    graph = nx.DiGraph()
    with open(location, 'r') as file:
        for line in file:
            connections = re.split(' -> {', line)
            if connections:
                predecessors = re.findall('\d+', connections[1])
                if len(predecessors) > treshold:
                    for elem in predecessors:
                        graph.add_edge(connections[0], elem)
    return graph


#loads the url file
def load_urls(location):
    urls = {}
    with open(location, 'r') as file:
        for line in file:
            data = re.split(';', line)
            if len(data) == 2:
                urls[data[0]] = data[1].strip(" \n")
    return urls


# loads the in-degree file
def load_indegrees(location):
    idgr = {}
    with open(location, 'r') as file:
        cntr = 0
        for line in file:
            data = re.split(';', line)
            idgr[data[0]] = (cntr, data[1].strip(" \n"))
            cntr += 1
    return idgr


# writes the analyser-results to a file
def write_results(location, pr, gscc, inc, outc, tenc, tubec, disc, indegrees, urls, num_of_nodes):
    with open(location, 'w') as file:
        file.write('PageRank;inDegreeRank;PageRankValue;inDegreeValue;Node id;Url;Type\n')
        for index, item in enumerate(pr):
            if item[0] not in indegrees:
                continue
            file.write(str(index)
                       + ';' + str(indegrees[item[0]][0])
                       + ';' + str(item[1])
                       + ';' + str(indegrees[item[0]][1])
                       + ';' + str(item[0])
                       + ';')
            if item[0] in urls:
                 file.write(urls[item[0]])
            if item[0] in gscc:
                 file.write(';gscc')
            elif item[0] in inc:
                 file.write(';in')
            elif item[0] in outc:
                 file.write(';out')
            elif item[0] in tenc:
                 file.write(';tendril')
            elif item[0] in tubec:
                 file.write(';tube')
            else:
                 file.write(';disconnected')
            file.write(newline)

        file.write(separator + newline)
        file.write('Number of nodes: ' + str(num_of_nodes) + newline)
        file.write('Huge scc (' + str(len(gscc)) + ' nodes - ' + str(100 * len(gscc) / float(num_of_nodes)) + '%):' + newline)
        file.write('\t' + str(gscc) + newline)
        file.write('In (' + str(len(inc)) + ' nodes - ' + str(100 * len(inc) / float(num_of_nodes)) + '%):' + newline)
        file.write('\t' + str(inc) + newline)
        file.write(separator + newline)
        file.write('Out (' + str(len(outc)) + ' nodes - ' + str(100 * len(outc) / float(num_of_nodes)) + '%):' + newline)
        file.write('\t' + str(outc) + newline)
        file.write(separator + newline)
        file.write('Tendrils (' + str(len(tenc)) + ' nodes - ' + str(100 * len(tenc) / float(num_of_nodes)) + '%):' + newline)
        file.write('\t' + str(tenc) + newline)
        file.write(separator + newline)
        file.write('Tubes (' + str(len(tubec)) + ' nodes - ' + str(100 * len(tubec) / float(num_of_nodes)) + '%):' + newline)
        file.write('\t' + str(tubec) + newline)
        file.write(separator + newline)
        file.write('Disconnected (' + str(len(disc)) + ' nodes - ' + str(100 * len(disc) / float(num_of_nodes)) + '%):' + newline)
        file.write('\t' + str(disc) + newline)

def write_items(file, items):
    for item in items:
        file.write(item + newline)

def print_process(text, current, total, interval):
    if interval > 0:
        if current % interval == 0:
            print(text, current, divider, total)