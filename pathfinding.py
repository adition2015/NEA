# --- Pathfinding ---

# -- imports --
import heapq, pygame, math
from grid_waypoint import Waypoint


# -- helper functions --

def distance(p1, p2):
    return p1.distance_to(p2)


# -- a-star ---

def a_star(graph, start: Waypoint, end: Waypoint):
    open_set = []
    heapq.heappush(open_set, (0, start))

    came_from = {}

    g_score = {start: 0}

    while open_set:
        current = heapq.heappop(open_set)[1]

        if current == end:
            path = []
            # iteratively adds from came_from the nodes the path takes in reverse order, except start
            # start is added later
            # path is reversed and returned for further use
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path
        
        for neighbour in current.neighbours:
            # calculating travel cost
            tentative = g_score[current] + distance(current.pos, neighbour.pos)

            # euclidean distance heuristic:
            if neighbour not in g_score or tentative < g_score[neighbour]:
                came_from[neighbour] = current
                g_score[neighbour] = tentative
                f = tentative + distance(neighbour.pos, end.pos)
                heapq.heappush(open_set, (f, neighbour))
    return None