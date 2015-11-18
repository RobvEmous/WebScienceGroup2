import networkx as nx
import tools
import time
from heapq import heappush, heappop
from itertools import count

class Analyzer():

    def yield_scc(self, graph):
        '''
        Yields all strongly connected components from @param graph
        :param graph:
        :return strongly connected components:
        '''
        return [node for node in nx.strongly_connected_components(graph)]

    def yield_gscc(self, scc):
        '''
        Yields the giant component from @param strongly connected components
        :param scc:
        :return giant component:
        '''
        gscc = max(scc, key=lambda x:len(x))
        scc.remove(gscc)
        return gscc

    def generate_pagerank(self, graph):
        '''
        Generates a list of tuples of nodes and their pagerank sorted on pagerank
        :param graph:
        :return a list of tuples of nodes and their pagerank:
        '''
        pr = nx.pagerank(graph, alpha=0.9)
        return sorted(pr.items(), key=lambda x:x[1])

    def generate_in_out(self, graph, scc, gscc, interval, print):
        '''
        Generates the in and out sets of @param graph and the strongly connected components which make up these sets.
        :param graph:
        :param scc:
        :param gscc:
        :param interval:
        :return inset, outset, inscc's, outscc's:
        '''
        inc, outc, incsubsets, outcsubsets = set(), set(), [], []
        gscc_node = next(iter(gscc))
        sccsize = len(scc)
        for index, c in enumerate(scc):
            if print:
                tools.print_process('Generating in & out sets: ', index, sccsize, interval)
            c_node = next(iter(c))
            if self.can_reach(graph, c_node, gscc_node):
                inc = inc.union(c)
                incsubsets.append(c)
                scc.remove(c)
            elif self.can_reach(graph, gscc_node, c_node):
                outc = outc.union(c)
                outcsubsets.append(c)
                scc.remove(c)
        return inc, incsubsets, outc, outcsubsets

    def generate_tend_tun_disc(self, graph, incsubsets, outcsubsets, scc, interval, print):
        tenc, tubec, disc = set(), set(), set()
        sccsize = len(scc)
        for index, c in enumerate(scc):
            c_node = next(iter(c))
            if print:
                tools.print_process('Generating tendrils & tube & disconnected sets: ', index, sccsize, interval)
            found = False
            for inc in incsubsets:
                in_node = next(iter(inc))
                if self.can_reach(graph, in_node, c_node):
                    for outc in outcsubsets:
                        out_node = next(iter(outc))
                        if self.can_reach(graph, c_node, out_node):
                            tubec = tubec.union(c)
                            found = True
                            break
                    if not found:
                        tenc = tenc.union(c)
                        found = True
                if found:
                    break
            if not found:
                for outc in outcsubsets:
                    out_node = next(iter(outc))
                    if self.can_reach(graph, c_node, out_node):
                        tenc = tenc.union(c)
                        found = True
                        break
                if not found:
                    disc = disc.union(c)
        return tenc, tubec, disc

    def path_exists_bi_dijkstra(self, G, source, target, weight = 'weight'):
        if source == target:
            return True

        push = heappush
        pop = heappop
        # Init:   Forward             Backward
        dists = [{}, {}]  # dictionary of final distances
        paths = [{source: [source]}, {target: [target]}]  # dictionary of paths
        fringe = [[], []]  # heap of (distance, node) tuples for
        # extracting next node to expand
        seen = [{source: 0}, {target: 0}]  # dictionary of distances to
        # nodes seen
        c = count()
        # initialize fringe heap
        push(fringe[0], (0, next(c), source))
        push(fringe[1], (0, next(c), target))
        # neighs for extracting correct neighbor information
        if G.is_directed():
            neighs = [G.successors_iter, G.predecessors_iter]
        else:
            neighs = [G.neighbors_iter, G.neighbors_iter]
        # variables to hold shortest discovered path
        # finaldist = 1e30000
        finalpath = []
        dir = 1
        while fringe[0] and fringe[1]:
            # choose direction
            # dir == 0 is forward direction and dir == 1 is back
            dir = 1 - dir
            # extract closest to expand
            (dist, _, v) = pop(fringe[dir])
            if v in dists[dir]:
                # Shortest path to v has already been found
                continue
            # update distance
            dists[dir][v] = dist  # equal to seen[dir][v]
            if v in dists[1 - dir]:
                # if we have scanned v in both directions we are done
                # we have now discovered the shortest path
                return True

            for w in neighs[dir](v):
                if (dir == 0):  # forward
                    if G.is_multigraph():
                        minweight = min((dd.get(weight, 1)
                                         for k, dd in G[v][w].items()))
                    else:
                        minweight = G[v][w].get(weight, 1)
                    vwLength = dists[dir][v] + minweight  # G[v][w].get(weight,1)
                else:  # back, must remember to change v,w->w,v
                    if G.is_multigraph():
                        minweight = min((dd.get(weight, 1)
                                         for k, dd in G[w][v].items()))
                    else:
                        minweight = G[w][v].get(weight, 1)
                    vwLength = dists[dir][v] + minweight  # G[w][v].get(weight,1)

                if w in dists[dir]:
                    if vwLength < dists[dir][w]:
                        raise ValueError(
                            "Contradictory paths found: negative weights?")
                elif w not in seen[dir] or vwLength < seen[dir][w]:
                    # relaxing
                    seen[dir][w] = vwLength
                    push(fringe[dir], (vwLength, next(c), w))
                    paths[dir][w] = paths[dir][v] + [w]
                    if w in seen[0] and w in seen[1]:
                        # see if this path is better than than the already
                        # discovered shortest path
                        totaldist = seen[0][w] + seen[1][w]
                        if finalpath == [] or finaldist > totaldist:
                            finaldist = totaldist
                            revpath = paths[1][w][:]
                            revpath.reverse()
                            finalpath = paths[0][w] + revpath[1:]
        return False

    def can_reach(self, graph, start, stop):
        return self.path_exists_bi_dijkstra(graph, start, stop)

    def my_print(self, pp, *txt):
        if pp:
            for tx in txt[:-1]:
                print(tx),
            print(txt[-1])

    def run(self, source, dest, treshold, pp):
        print_interval = 100
        start_time = time.time()
        graph = tools.load_graph(source, treshold)
        self.my_print(pp, 'Graph loaded from ', source)

        pr = self.generate_pagerank(graph)
        self.my_print(pp, 'Pagerank calculated')

        scc = self.yield_scc(graph)
        self.my_print(pp, 'Found scc\'s - amount = ', len(scc))

        gscc = self.yield_gscc(scc)
        self.my_print(pp, 'Found scc\'s - len = ', len(gscc))

        inc, incsubsets, outc, outcsubsets = self.generate_in_out(graph, scc, gscc, print_interval, pp)
        self.my_print(pp, 'Found the in & out sets')

        tenc, tubec, disc = self.generate_tend_tun_disc(graph, incsubsets, outcsubsets, scc, print_interval, pp)
        self.my_print(pp, 'Found tendrils & tube & disconnected sets')

        tools.write_results(dest, pr, inc, outc, tenc, tubec, disc)
        self.my_print(pp, 'Writing results to ', dest)
        elapsed_time = time.time() - start_time
        self.my_print(pp, 'Time duration ', elapsed_time, 's')

an = Analyzer()
an.run('Input/edges.dot', 'Output/utwente_result.txt', 100, True)



