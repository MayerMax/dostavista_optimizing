import json

from data_wrappers import Courier, Order
from collections import namedtuple

CompletedOrderInfo = namedtuple('OrderInfo', ['courier_id', 'order_id', 'revenue'])


class OneStepGreedy:
    def __init__(self, data_path):
        with open(data_path) as f:
            data = json.loads(f.read())

        self._couriers = [Courier(x) for x in data['couriers']]
        self._orders = [Order(x) for x in data['orders']]

        self._orders_map = {order.order_id: order for order in self._orders}
        self._couriers_map = {courier.id: courier for courier in self._couriers}

        self._orders_immutable_map = {order.order_id: order for order in self._orders}

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

        return 2 * (arrives_to_dropoff_point - initial_time)

    def solve(self):
        completed_orders = []
        total_revenue = 0

        while True and len(self._orders) > 0:
            found_positive_revenues = [self._find_optimal_courier_step(c) for c in self._couriers]
            found_positive_revenues.sort(key=lambda x: x.revenue, reverse=True)
            if found_positive_revenues[0].revenue < 0:  # most optimal revenue is negative
                break

            total_revenue += found_positive_revenues[0].revenue

            cur_order_info = found_positive_revenues[0]
            courier = self._couriers_map[cur_order_info.courier_id]
            order = self._orders_map.pop(cur_order_info.order_id)

            arrives_to_dropoff_point = self.time_when_dropoffs_of(self.time_when_picks_up(courier, order), order)
            courier.update_current_time(arrives_to_dropoff_point)
            courier.update_current_pos(order.dropoff_location_x, order.dropoff_location_y)

            completed_orders.append(found_positive_revenues[0])
            print('Update records, num: {}'.format(len(completed_orders)))

        answer = []
        for record in completed_orders:
            answer.append({
                'courier_id': record.courier_id,
                'action': 'pickup',
                'order_id': record.order_id,
                'point_id': self._orders_immutable_map[record.order_id].pickup_point_id
            })

            answer.append({
                'courier_id': record.courier_id,
                'action': 'dropoff',
                'order_id': record.order_id,
                'point_id': self._orders_immutable_map[record.order_id].dropoff_point_id
            })
        return answer

    def _find_optimal_courier_step(self, courier):
        variants = []
        for key in self._orders_map:
            revenue = self.revenue_from_completing_order(courier, self._orders_map[key])
            if revenue > 0:
                variants.append(CompletedOrderInfo(courier.id, self._orders_map[key].order_id, revenue))
        if not variants:
            return CompletedOrderInfo(courier.id, -1, float('-inf'))

        variants.sort(key=lambda x: x.revenue, reverse=True)
        if variants[0].revenue < 0:  # revenue at most optimal point
            return CompletedOrderInfo(courier.id, -1, float('-inf'))
        return variants[0]


if __name__ == '__main__':
    solver = OneStepGreedy('../example/contest_input.json')
    with open('../example/contest_output.json', 'w') as outfile:
        json.dump(solver.solve(), outfile)