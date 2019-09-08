import json
import random

from data_wrappers import Courier, Order
from collections import namedtuple

CompletedOrderInfo = namedtuple('OrderInfo', ['courier_id', 'order_id', 'revenue'])


def calculate_manhattan_dist(order: Order):
    return abs(order.pickup_location_x - order.dropoff_location_x) + abs(
        order.pickup_location_y - order.dropoff_location_y)


class GreedyByUserAtN:
    def __init__(self, data_path):
        with open(data_path) as f:
            data = json.loads(f.read())

        self._orders_map = {order.order_id: order for order in [Order(x) for x in data['orders']]}
        print(len(self._orders_map))

        self._couriers = [Courier(x) for x in data['couriers']]
        random.shuffle(self._couriers)

        self._orders_immutable_map = {order.order_id: order for order in [Order(x) for x in data['orders']]}

    @staticmethod
    def time_when_picks_up(courier: Courier, order: Order):
        if not courier.get_current_time():
            return None

        if courier.get_current_time() > order.pickup_to:
            return None

        arrives_to_point_at = courier.get_current_time() + 10 + abs(courier.location_x - order.pickup_location_x) + abs(
            courier.location_y - order.pickup_location_y)

        if arrives_to_point_at > order.pickup_to:
            return None
        if arrives_to_point_at < order.pickup_from:
            arrives_to_point_at += order.pickup_from - arrives_to_point_at
        return arrives_to_point_at

    @staticmethod
    def time_when_dropoffs_of(courier_actual_time: int, order: Order):
        if not courier_actual_time:
            return None
        if courier_actual_time > order.dropoff_to:
            return None

        arrives_to_point_at = courier_actual_time + 10 + abs(order.pickup_location_x - order.dropoff_location_x) + abs(
            order.pickup_location_y - order.dropoff_location_y)

        if arrives_to_point_at > order.dropoff_to:
            return None

        if arrives_to_point_at < order.dropoff_from:
            arrives_to_point_at += order.dropoff_from - arrives_to_point_at
        return arrives_to_point_at

    def revenue_from_completing_order(self, courier: Courier, order: Order):
        initial_time = courier.get_current_time()
        arrives_to_pick_up_point = self.time_when_picks_up(courier, order)

        if not arrives_to_pick_up_point:
            return float('-inf')

        arrives_to_dropoff_point = self.time_when_dropoffs_of(arrives_to_pick_up_point, order)
        if not arrives_to_dropoff_point:
            return float('-inf')

        return order.payment - 2 * (arrives_to_dropoff_point - initial_time)

    def solve(self):
        answer = []
        num_orders_total = 0
        for idx, courier in enumerate(self._couriers):
            orders = self._find_courier_path(courier)
            answer.extend(orders)
            num_orders_total += len(orders)
            print('Processed courier, {}, num_orders: {}'.format(idx, len(orders)))
        print('Num total orders completed {}'.format(len(answer)))
        return answer

    def _find_courier_path(self, courier: Courier):
        paths = []
        answer = []

        while True:
            possible_revenues = {key: self.revenue_from_completing_order(courier, self._orders_map[key]) for key in
                                 self._orders_map}
            constructed_path = []
            max_revenue_value = float('-inf')

            for key in possible_revenues:
                print(key)
                order = self._orders_map[key]
                revenue_from_point = possible_revenues[key]
                second_point_id, second_point_revenue = self._simulate_2nd_transition(courier, order)
                if not second_point_revenue:
                    continue

                found_revenue = max(revenue_from_point + second_point_revenue, revenue_from_point)
                if found_revenue > max_revenue_value:
                    if found_revenue == revenue_from_point + second_point_revenue:
                        constructed_path = [key, second_point_id]

                    else:
                        constructed_path = [key]

                    max_revenue_value = found_revenue

            if max_revenue_value < 0:
                break

            if constructed_path:
                first_order = self._orders_map.pop(constructed_path[0])
                second_order = None
                if len(constructed_path) > 1:
                    second_order = self._orders_map.pop(constructed_path[1])

                self._make_courier_transition(courier, first_order)
                paths.append(first_order)

                if second_order:
                    self._make_courier_transition(courier, second_order)
                    paths.append(second_order)

        for order in paths:
            answer.append({
                'courier_id': courier.id,
                'action': 'pickup',
                'order_id': order.order_id,
                'point_id': order.pickup_point_id
            })

            answer.append({
                'courier_id': courier.id,
                'action': 'dropoff',
                'order_id': order.order_id,
                'point_id': order.dropoff_point_id
            })

        return answer

    def _make_courier_transition(self, courier, order):
        arrives_to_dropoff_point = self.time_when_dropoffs_of(self.time_when_picks_up(courier, order),
                                                              order)
        courier.update_current_time(arrives_to_dropoff_point)
        courier.update_current_pos(order.dropoff_location_x, order.dropoff_location_y)

    def _simulate_2nd_transition(self, courier, found_order: Order):
        courier_initial_time = courier.get_current_time()
        courier_initial_x = courier.location_x
        courier_initial_y = courier.location_y

        if not courier.get_current_time():
            return float('-inf'), None

        self._make_courier_transition(courier, found_order)

        new_possible_revenues = {key: self.revenue_from_completing_order(courier, self._orders_map[key]) for key in
                                 self._orders_map if key != found_order.order_id}

        max_revenue_id = None
        max_revenue_value = float('-inf')

        for key in new_possible_revenues:
            if new_possible_revenues[key] > max_revenue_value:
                max_revenue_id = key
                max_revenue_value = new_possible_revenues[key]

        courier.update_current_time(courier_initial_time)
        courier.update_current_pos(courier_initial_x, courier_initial_y)

        if max_revenue_value < 0:
            return float('-inf'), None

        return max_revenue_id, max_revenue_value


if __name__ == '__main__':
    solver = GreedyByUserAtN('../example/input.json')
    with open('../example/output.json', 'w') as outfile:
        json.dump(solver.solve(), outfile)
