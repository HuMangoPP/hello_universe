import numpy as np
import pygame as pg

class QuadTree:
    def __init__(self, center: np.ndarray, length: float, capacity: int):
        self.capacity = capacity
        self.center = center
        self.length = length

        self.clear()

    def insert(self, point: np.ndarray, index: int):

        if self.indices.size < self.capacity:
            self.points = np.array([*self.points, point])
            self.indices = np.array([*self.indices, index])
        else:
            if not self.divided:
                self.subdivide()
            
            if point[0] <= self.center[0] and point[1] <= self.center[1]:
                self.northwest.insert(point, index)
            elif point[0] >= self.center[0] and point[1] <= self.center[1]:
                self.northeast.insert(point, index)
            elif point[0] <= self.center[0] and point[1] >= self.center[1]:
                self.southwest.insert(point, index)
            else:
                self.southeast.insert(point, index)
    
    def subdivide(self):
        self.northwest = QuadTree(self.center - np.array([self.length,self.length])/2, self.length/2, self.capacity)
        self.northeast = QuadTree(self.center + np.array([self.length,-self.length])/2, self.length/2, self.capacity)
        self.southwest = QuadTree(self.center + np.array([-self.length,self.length])/2, self.length/2, self.capacity)
        self.southeast = QuadTree(self.center + np.array([self.length,self.length])/2, self.length/2, self.capacity)
        self.divided = True
    
    def query_point(self, xy: np.ndarray, boxradius: float) -> np.ndarray:
        if (self.center[0] + self.length < xy[0] - boxradius or 
            self.center[0] - self.length > xy[0] + boxradius or
            self.center[1] + self.length < xy[1] - boxradius or
            self.center[1] - self.length > xy[1] + boxradius):
            # the boundaries do not intersect
            return np.array([], np.float32)

        points_within_boundary = np.array([p for p in self.points 
                                           if (xy[0] - boxradius <= p[0] and 
                                               p[0] <= xy[0] + boxradius and
                                               xy[1] - boxradius <= p[1] and
                                               p[1] <= xy[1] + boxradius)], np.float32)
        if self.divided:
            quadrants = [self.northwest,self.northeast,self.southwest,self.southeast]
            for q in quadrants:
                points_within_boundary = np.array([*points_within_boundary, *q.query_point(xy, boxradius)], np.float32)

        return points_within_boundary

    def query_indices(self, xy: np.ndarray, boxradius: float) -> np.ndarray:
        if (self.center[0] + self.length < xy[0] - boxradius or 
            self.center[0] - self.length > xy[0] + boxradius or
            self.center[1] + self.length < xy[1] - boxradius or
            self.center[1] - self.length > xy[1] + boxradius):
            # the boundaries do not intersect
            return np.array([], np.int32)
        
        points_within_boundary = np.array([index for p, index in zip(self.points, self.indices)
                                           if (xy[0] - boxradius <= p[0] and 
                                               p[0] <= xy[0] + boxradius and
                                               xy[1] - boxradius <= p[1] and
                                               p[1] <= xy[1] + boxradius)], np.int32)
        if self.divided:
            quadrants = [self.northwest,self.northeast,self.southwest,self.southeast]
            for q in quadrants:
                points_within_boundary = np.array([*points_within_boundary, *q.query_indices(xy, boxradius)], np.int32)

        return points_within_boundary

    def clear(self):
        self.points = np.array([], np.float32) # (n,3)
        self.indices = np.array([], np.int32) # (n,)

        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None
        self.divided = False

    def render(self, display: pg.Surface):
        boundary = pg.Rect(0, 0, self.length*2, self.length*2)
        boundary.center = tuple(self.center)
        pg.draw.rect(display, (255,255,255), boundary, 1)
        # [pg.draw.circle(display, (255,255,255), point, 3)
        #  for point in self.points]
        if self.divided:
            self.northwest.render(display)
            self.northeast.render(display)
            self.southwest.render(display)
            self.southeast.render(display)

def intersects(p: np.ndarray, op: np.ndarray, radius: float) -> bool:
    dist = np.linalg.norm(p - op)
    return 0 < dist and dist <= r * 2


if __name__ == '__main__':
    r = 5
    pg.init()
    res = (400, 400)
    display = pg.display.set_mode(res)
    clock = pg.time.Clock()

    points = np.array([np.random.rand(2) * 400
                       for _ in range(100)])

    running = True
    while running:

        # point update
        points = points + (np.random.rand(points.shape[0], points.shape[1])*2-1)
        qt = QuadTree(np.array([200,200]), 200, 4)
        [qt.insert(p) for p in points]

        # render
        display.fill((0, 0, 0))

        qt.render(display)
        # [pg.draw.circle(display, (255, 255, 255), point, 3)
        #  for point in points]
        for p in points:
            others = qt.query_point(np.array([p[0],p[1],r*2]))
            others = np.array([op for op in others 
                               if intersects(p, op, r)])
            if others.size > 0:
                pg.draw.circle(display, (0, 255, 0), p, r)
            else:
                pg.draw.circle(display, (255, 255, 255), p, r)

        pg.display.flip()
        clock.tick()

        pg.display.set_caption(f'FPS: {clock.get_fps()}')

        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit()
                running = False
            if event.type == pg.KEYDOWN and event.key == pg.K_ESCAPE:
                pg.quit()
                running = False
