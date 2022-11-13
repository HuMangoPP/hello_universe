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