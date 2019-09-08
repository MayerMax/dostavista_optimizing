import json
import numpy as np
import sys
import random

from data_wrappers import Courier, Order
from collections import namedtuple

CompletedOrderInfo = namedtuple('OrderInfo', ['courier_id', 'order_id', 'revenue'])


class GreedyByUser:
    def __init__(self, data_path):
        with open(data_path) as f:
            data = json.loads(f.read())

        self._orders_map = {order.order_id: order for order in [Order(x) for x in data['orders']]}

        self._couriers = [Courier(x) for x in data['couriers']]
        random.shuffle(self._couriers)

        self._orders_immutable_map = {order.order_id: order for order in [Order(x) for x in data['orders']]}

    @staticmethod
    def time_when_picks_up(courier: Courier, order: Order):
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
        was_negative = False
        while True:
            possible_revenues = {key: self.revenue_from_completing_order(courier, self._orders_map[key]) for key in
                                 self._orders_map}
            max_revenue_id = None
            max_revenue_value = float('-inf')
            for key in possible_revenues:
                if possible_revenues[key] > max_revenue_value:
                    max_revenue_id = key
                    max_revenue_value = possible_revenues[key]

            if max_revenue_value <= 0 and was_negative:
                break

            if max_revenue_value <= 0 and max_revenue_value == float('-inf') :
                break

            if max_revenue_value <= 0 and not was_negative:
                was_negative = True

            new_order = self._orders_map.pop(max_revenue_id)
            arrives_to_dropoff_point = self.time_when_dropoffs_of(self.time_when_picks_up(courier, new_order),
                                                                  new_order)
            courier.update_current_time(arrives_to_dropoff_point)
            courier.update_current_pos(new_order.dropoff_location_x, new_order.dropoff_location_y)

            paths.append(new_order)

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


if __name__ == '__main__':
    solver = GreedyByUser('../example/contest_input.json')
    with open('../example/contest_output_greedy_by_user.json', 'w') as outfile:
        json.dump(solver.solve(), outfile)