import json
import numpy as np
import sys
from munkres import Munkres, make_cost_matrix, DISALLOWED

from data_wrappers import Courier, Order
from collections import namedtuple

CompletedOrderInfo = namedtuple('OrderInfo', ['courier_id', 'order_id', 'revenue'])


class HungarianSearch:
    def __init__(self, data_path):
        with open(data_path) as f:
            data = json.loads(f.read())

        self._couriers = [Courier(x) for x in data['couriers']]
        self._orders = [Order(x) for x in data['orders']]

        self._orders_immutable_map = {order.order_id: order for order in self._orders}

        self.m = Munkres()

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
        num_rounds = 0
        answer = []

        while True:
            new_match = self._find_optimal_match()
            if not new_match:
                break
            used_orders = set()
            completed_orders = []

            for row, column in new_match:
                courier = self._couriers[row]
                order = self._orders[column]

                arrives_to_dropoff_point = self.time_when_dropoffs_of(self.time_when_picks_up(courier, order), order)
                courier.update_current_time(arrives_to_dropoff_point)
                courier.update_current_pos(order.dropoff_location_x, order.dropoff_location_y)
                completed_orders.append((courier, order))
                used_orders.add(column)

            self._orders = [x for idx, x in enumerate(self._orders) if idx not in used_orders]

            for courier, order in completed_orders:
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

            num_rounds += 1
            print('Rounds completed: {}'.format(num_rounds))
            with open('../example/output_{}.json'.format(num_rounds), 'w') as outfile:
                json.dump(answer, outfile)
        return answer

    def _find_optimal_match(self):
        matrix = [[0 for _ in range(len(self._orders))] for _ in range(len(self._couriers))]
        viewed_rows = {i: 0 for i in range(len(self._couriers))}

        for i, courier in enumerate(self._couriers):
            for j, order in enumerate(self._orders):
                revenue_from_completion = self.revenue_from_completing_order(courier, order)
                if revenue_from_completion == float('-inf'):
                    matrix[i][j] = DISALLOWED
                else:
                    matrix[i][j] = revenue_from_completion
        elements_to_remove = [x for x in viewed_rows if viewed_rows[x] == len(self._orders)]
        matrix = np.delete(matrix, elements_to_remove, axis=0)
        if elements_to_remove:
            self._couriers = [x for idx, x in enumerate(self._couriers) if idx not in elements_to_remove]
        if matrix.size == 0:
            return None

        cost_matrix = make_cost_matrix(matrix,
                                       lambda cost: (sys.maxsize - cost) if (cost != DISALLOWED) else DISALLOWED)
        indexes = self.m.compute(cost_matrix)
        if not indexes:
            return None
        return indexes


if __name__ == '__main__':
    solver = HungarianSearch('../example/contest_input.json')
    solver.solve()
    # with open('../example/contest_output.json', 'w') as outfile:
    #     json.dump(solver.solve(), outfile)
