"""Original interview prompts for the candidate workspace."""

PROBLEMS = (
    {
        "id": "locker-utilization",
        "title": "Locker Utilization",
        "prompt": (
            "A pickup hub reserves lockers for parcels. Each reservation is a "
            "pair [start, end] of integer minutes and occupies one locker on "
            "the half-open interval [start, end). Return the minimum number of "
            "lockers needed and the earliest minute at which that many are "
            "occupied. Return (0, None) for an empty list."
        ),
        "constraints": "0 <= number of reservations <= 200,000. "
        "0 <= start < end <= 10^9. Reservations may arrive in any order.",
        "example": "[(5, 9), (1, 5), (4, 7), (5, 8)] -> (3, 5)",
        "starter_code": "def locker_utilization(reservations):\n    pass\n",
    },
    {
        "id": "returns-routing",
        "title": "Returns Routing",
        "prompt": (
            "A returns network has warehouses numbered from 0 to n - 1. "
            "Each link [u, v, minutes] is directed. Given a starting "
            "warehouse and a set of inspection warehouses, return the ID "
            "of the reachable inspection warehouse with the shortest total "
            "travel time. Break ties by smaller ID. Return -1 if none is "
            "reachable. The starting warehouse is eligible if it is listed."
        ),
        "constraints": "1 <= n <= 100,000. At most 250,000 links. "
        "Each travel time is an integer from 1 to 10^6. Parallel links are allowed.",
        "example": "n=4, links=[(0, 1, 5), (0, 2, 2), (2, 1, 1), (2, 3, 1)], "
        "start=0, inspection={1, 3} -> 1",
        "starter_code": "def returns_routing(n, links, start, inspection):\n    pass\n",
    },
    {
        "id": "packing-lanes",
        "title": "Packing Lanes",
        "prompt": (
            "A packing lane must process orders in the given sequence. For "
            "one shift, choose a consecutive range of orders whose total "
            "packing time fits the shift budget. Return the range with the "
            "most orders as (start, end), using zero-based indices and an "
            "exclusive end. Break ties by earliest start. Return (0, 0) "
            "if no order fits."
        ),
        "constraints": "0 <= number of orders <= 200,000. Each packing time is "
        "an integer from 1 to 10^6. The budget is an integer from 0 to 10^12.",
        "example": "times=[4, 2, 1, 3, 2], budget=6 -> (1, 4)",
        "starter_code": "def packing_lanes(times, budget):\n    pass\n",
    },
)
