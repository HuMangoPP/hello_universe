import numpy as np
import pygame as pg

class QuadTree:
    def __init__(self, center: np.ndarray, length: float, capacity: int):
        self.capacity = capacity
        self.center = center
        self.length = length
        self.points = np.array([])
        self.data = []
        self.divided = False

    def insert(self, point: np.ndarray, data: float=0):

        # if not self.contains(point):
        #     return
        
        if self.points.size == 0:
            self.points = np.array([point])
            self.data = [data]
        elif self.points.shape[0] < self.capacity:
            self.points = np.concatenate([self.points, np.array([point])])
            self.data.append(data)
        else:
            if not self.divided:
                self.subdivide()
            if point[0] <= self.center[0] and point[1] <= self.center[1]:
                self.northwest.insert(point, data)
            elif point[0] >= self.center[0] and point[1] <= self.center[1]:
                self.northeast.insert(point, data)
            elif point[0] <= self.center[0] and point[1] >= self.center[1]:
                self.southwest.insert(point, data)
            else:
                self.southeast.insert(point, data)
    
    def subdivide(self):
        self.northwest = QuadTree(self.center - np.array([self.length,self.length])/2, self.length/2, self.capacity)
        self.northeast = QuadTree(self.center + np.array([self.length,-self.length])/2, self.length/2, self.capacity)
        self.southwest = QuadTree(self.center + np.array([-self.length,self.length])/2, self.length/2, self.capacity)
        self.southeast = QuadTree(self.center + np.array([self.length,self.length])/2, self.length/2, self.capacity)
        self.divided = True
    
    def query_point(self, boundary: np.ndarray) -> np.ndarray:
        if (self.center[0] + self.length < boundary[0] - boundary[2] or 
            self.center[0] - self.length > boundary[0] + boundary[2] or
            self.center[1] + self.length < boundary[1] - boundary[2] or
            self.center[1] - self.length > boundary[1] + boundary[2]):
            return np.array([])

        points_within_boundary = np.array([p for p in self.points 
                                           if (boundary[0] - boundary[2] <= p[0] and 
                                               p[0] <= boundary[0] + boundary[2] and
                                               boundary[1] - boundary[2] <= p[1] and
                                               p[1] <= boundary[1] + boundary[2])])
        if self.divided:
            quadrants = [self.northwest,self.northeast,self.southwest,self.southeast]
            for q in quadrants:
                points_within_quadrant = q.query_point(boundary)
                if points_within_quadrant.size > 0:
                    if points_within_boundary.size > 0:
                        points_within_boundary = np.concatenate([points_within_boundary, points_within_quadrant])
                    else:
                        points_within_boundary = points_within_quadrant

    
        return points_within_boundary

    def query_data(self, boundary: np.ndarray) -> list:
        if (self.center[0] + self.length < boundary[0] - boundary[2] or 
            self.center[0] - self.length > boundary[0] + boundary[2] or
            self.center[1] + self.length < boundary[1] - boundary[2] or
            self.center[1] - self.length > boundary[1] + boundary[2]):
            return []

        points_within_boundary = [data for p, data in zip(self.points, self.data) 
                                           if (boundary[0] - boundary[2] <= p[0] and 
                                               p[0] <= boundary[0] + boundary[2] and
                                               boundary[1] - boundary[2] <= p[1] and
                                               p[1] <= boundary[1] + boundary[2])]
        if self.divided:
            quadrants = [self.northwest,self.northeast,self.southwest,self.southeast]
            for q in quadrants:
                points_within_quadrant = q.query_data(boundary)
                points_within_boundary = points_within_boundary + points_within_quadrant

        return points_within_boundary

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
