def accelerate(direction, acceleration, current_speed):
    if direction>0:
        current_speed+=direction*acceleration
    elif direction<0:
        current_speed+=direction*acceleration
    
    return current_speed

def de_accelerate(acceleration, current_speed):
    if current_speed>0:
        current_speed-=acceleration
        if current_speed<0:
            return 0
    elif current_speed<0:
        current_speed+=acceleration
        if current_speed>0:
            return 0
    
    return current_speed

def collide(p1, p2):
    sq_dist = (p1[0]-p2[0])**2
    sq_dist+=(p1[1]-p2[1])**2
    sq_dist+=(p1[2]-p2[2])**2
    
    return sq_dist<=(p1[3]+p2[3])**2