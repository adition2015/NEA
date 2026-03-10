# --- Pathfinding ---

# -- imports --
import heapq, pygame
from grid_waypoint import Waypoint


# -- helper functions --

def distance(p1, p2):
    if isinstance(p1, Waypoint):
        p1 = p1.pos
    if isinstance(p2, Waypoint):
        p2 = p2.pos
    p1 = pygame.Vector2(p1)
    p2 = pygame.Vector2(p2)
    return p1.distance_to(p2)


# -- a-star ---

def a_star(start: Waypoint, end: Waypoint):
    open_set = []
    counter = 0
    heapq.heappush(open_set, (0, counter, start))
    counter += 1

    came_from = {}

    g_score = {start: 0}

    while open_set:
        current = heapq.heappop(open_set)[2]

        if current == end:
            path = []
            # iteratively adds from came_from the nodes the path takes in reverse order, except start
            # start is added later
            # path is reversed and returned for further use
            while current in came_from:
                path.append(current.pos)
                current = came_from[current]
            path.append(start.pos)
            path.reverse()
            return path
        
        for neighbour in current.neighbours:
            # calculating travel cost
            tentative = g_score[current] + distance(current, neighbour)

            # euclidean distance heuristic:
            if neighbour not in g_score or tentative < g_score[neighbour]:
                came_from[neighbour] = current
                g_score[neighbour] = tentative
                f = tentative + distance(neighbour, end)
                heapq.heappush(open_set, (f, counter, neighbour))
                counter += 1
    return None