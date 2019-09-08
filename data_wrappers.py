INITIAL_TIME_CONSTANT = 360

class Courier:
    def __init__(self, data):
        self.id = data['courier_id']
        self.location_x = data['location_x']
        self.location_y = data['location_y']
        self._current_time = INITIAL_TIME_CONSTANT

    def update_current_time(self, new_time):
        self._current_time = new_time

    def update_current_pos(self, new_x, new_y):
        self.location_x = new_x
        self.location_y = new_y

    def get_current_time(self):
        return self._current_time


class Order:
    def __init__(self, data):
        self.order_id = data['order_id']
        self.pickup_point_id = data['pickup_point_id']
        self.pickup_location_x = data['pickup_location_x']
        self.pickup_location_y = data['pickup_location_y']
        self.pickup_from = data['pickup_from']
        self.pickup_to = data['pickup_to']
        self.dropoff_point_id = data['dropoff_point_id']
        self.dropoff_location_x = data['dropoff_location_x']
        self.dropoff_location_y = data['dropoff_location_y']
        self.dropoff_from = data['dropoff_from']
        self.dropoff_to = data['dropoff_to']
        self.payment = data['payment']