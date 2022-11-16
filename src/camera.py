from src.settings import WIDTH, HEIGHT

class Camera():
    def __init__(self, x, y):
        self.x = x
        self.y = y

        self.x_transform = [1, 0.5]
        self.y_transform = [-1, 0.5]
        self.x_inverse = [0.5, -0.5]
        self.y_inverse = [1, 1]

    def world_to_screen(self, x, y, z):
        return (x*self.x_transform[0]+y*self.y_transform[0],
                x*self.x_transform[1]+y*self.y_transform[1]-z)

    def camera_to_screen(self):
        return (self.x*self.x_transform[0]+self.y*self.y_transform[0],
                self.x*self.x_transform[1]+self.y*self.y_transform[1])

    def transform_to_screen(self, x, y, z):
        x_pos, y_pos = self.world_to_screen(x, y, z)
        camera_x, camera_y = self.camera_to_screen()
        return (x_pos-camera_x, y_pos-camera_y)

    def screen_to_world(self, x, y):
        return (x*self.x_inverse[0]+y*self.y_inverse[0],
                x*self.x_inverse[1]+y*self.y_inverse[1])

    def update(self, entities, following):
        # solved via a system of equations
        # we see that: WIDTH//2 = x - y
        # and          HEIGHT   = x + y
        # to keep the player centered
        self.x = entities.pos[following][0]-(HEIGHT//2+WIDTH//4)
        self.y = entities.pos[following][1]-(HEIGHT//2-WIDTH//4)