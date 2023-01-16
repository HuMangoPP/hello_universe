def new_vel(a, v, dir, dt):
    if dir>0:
        return v+a*dt
    elif dir<0:
        return v-a*dt
    elif v>a*dt:
        return v-a*dt
    elif v<-a*dt:
        return v+a*dt
    else:
        return 0

def collide(p1, p2):
    sq_dist = (p1[0]-p2[0])**2
    sq_dist+=(p1[1]-p2[1])**2
    sq_dist+=(p1[2]-p2[2])**2
    
    return sq_dist<=(p1[3]+p2[3])**2