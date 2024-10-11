import math

class wheel:
    def  __init__(self, vec_position : tuple, vec_basis_velocity : tuple):
        self.vec_position = vec_position
        self.vec_basis_velocity = vec_basis_velocity

        v2 = vec_basis_velocity[0]**2 + vec_basis_velocity[1]**2
        self.calc_position = (vec_position[0],vec_position[1])
        self.calc_basis_velocity = (vec_basis_velocity[0]/v2,vec_basis_velocity[1]/v2)

    def calc(self, vec_velocity : tuple, rotation_power : float)->float:
        straight_power = 1 - abs(rotation_power)
        output = straight_power*(vec_velocity[0]*self.calc_basis_velocity[0]+vec_velocity[1]*self.calc_basis_velocity[1])
        output += rotation_power*(-self.calc_basis_velocity[0]*self.calc_position[1]+self.calc_basis_velocity[1]*self.calc_position[0])
        # output *= 0.7
        return output

class omni(wheel):
    def __init__(self, vec_position: tuple, vec_basis_velocity: tuple):
        super().__init__(vec_position, vec_basis_velocity)

class mecanum_left(wheel):
    def __init__(self, vec_position: tuple, vec_basis_velocity: tuple):
        super().__init__(vec_position, vec_basis_velocity)
        self.calc_basis_velocity = (self.calc_basis_velocity[0]+self.calc_basis_velocity[1],-self.calc_basis_velocity[0]+self.calc_basis_velocity[1])

class mecanum_right(wheel):
    def __init__(self, vec_position: tuple, vec_basis_velocity: tuple):
        super().__init__(vec_position, vec_basis_velocity)
        self.calc_basis_velocity = (self.calc_basis_velocity[0]-self.calc_basis_velocity[1],self.calc_basis_velocity[0]+self.calc_basis_velocity[1])

class wheels:
    def __init__(self,wheels : tuple):
        self.wheels = wheels

    def calc(self, vec_velocity : tuple, rotation_power : float)->list:
        return[w.calc(vec_velocity, rotation_power)for w in self.wheels]