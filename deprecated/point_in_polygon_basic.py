def point_in_polygon(x, y, polygon):

    n = len(polygon)  # number of vertices
    inside = False    # assume outside until proven otherwise
    j = n - 1         # j trails i by one, starting at the last vertex
                      # so the first edge checked is (last vertex → first vertex),
                      # ensuring the polygon is closed

    for i in range(n):

        xi, yi = polygon[i]  # unpack current vertex
        xj, yj = polygon[j]  # unpack previous vertex — together these define the current edge

        # condition 1: does this edge straddle the test point vertically?
        # one vertex must be above y and the other below — if both are on
        # the same side, this edge cannot cross the horizontal ray
        vertically_straddles = (yi > y) != (yj > y)

        # condition 2: compute where the edge crosses the test point's y-level,
        # then check whether that crossing is to the right of the test point
        ray_hits = x < (xj - xi) * (y - yi) / (yj - yi) + xi

        if vertically_straddles and ray_hits:
            inside = not inside  # each valid crossing flips the state

        j = i  # advance j to trail i on the next iteration

    return inside



