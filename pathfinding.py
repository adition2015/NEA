import pygame



def seg_intersects_rect(a: pygame.Vector2, b: pygame.Vector2,
                         r: pygame.Rect) -> bool:
    """
    Returns True if segment a->b intersects (expanded) rect.
    Uses Liang-Barsky clipping algorithm.
    """

    dx, dy = b.x - a.x, b.y - a.y

    p = [-dx, dx, -dy, dy]
    q = [a.x - r.left, r.right - a.x, a.y - r.top, r.bottom - a.y]

    t0, t1 = 0.0, 1.0
    for pi, qi in zip(p, q):
        if pi == 0:
            if qi < 0:
                return False        # parallel and outside
        elif pi < 0:
            t0 = max(t0, qi / pi)
        else:
            t1 = min(t1, qi / pi)

    return t0 <= t1


def line_of_sight(a: pygame.Vector2, b: pygame.Vector2,
                   walls) -> bool:
    """True if the line a->b is unobstructed by any wall."""
    for wall in walls:
        if seg_intersects_rect(a, b, wall.rect):
            return False
    return True