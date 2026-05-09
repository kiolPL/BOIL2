import unittest

from backend.transport_solver import solve_transport_problem


class TransportSolverTests(unittest.TestCase):
    def test_northwest_corner_transport(self):
        result = solve_transport_problem(
            {
                "mode": "transport",
                "supplierCount": 2,
                "receiverCount": 2,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2"],
                "supply": [20, 30],
                "demand": [10, 40],
                "costs": [[2, 3], [4, 5]],
                "blocked": [[False, False], [False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["allocations"], [[10, 10], [0, 30]])
        self.assertEqual(result["totalCost"], 200)
        self.assertEqual(len(result["iterations"]), 3)

    def test_transport_profit_is_calculated_from_revenues(self):
        result = solve_transport_problem(
            {
                "mode": "transport",
                "supplierCount": 2,
                "receiverCount": 2,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2"],
                "supply": [20, 30],
                "demand": [10, 40],
                "costs": [[2, 3], [4, 5]],
                "revenues": [[9, 8], [7, 11]],
                "blocked": [[False, False], [False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["totalCost"], 200)
        self.assertEqual(result["totalRevenue"], 500)
        self.assertEqual(result["totalProfit"], 300)
        self.assertEqual(result["routeSummary"][0]["revenue"], 90)
        self.assertEqual(result["routeSummary"][0]["profit"], 70)
        self.assertEqual(result["iterations"][-1]["totalProfitSoFar"], 300)

    def test_profit_can_be_disabled(self):
        result = solve_transport_problem(
            {
                "mode": "transport",
                "calculateProfit": False,
                "supplierCount": 2,
                "receiverCount": 2,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2"],
                "supply": [20, 30],
                "demand": [10, 40],
                "costs": [[2, 3], [4, 5]],
                "revenues": [[9, 8], [7, 11]],
                "blocked": [[False, False], [False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertFalse(result["profitEnabled"])
        self.assertEqual(result["totalCost"], 200)
        self.assertIsNone(result["totalRevenue"])
        self.assertIsNone(result["totalProfit"])
        self.assertNotIn("revenue", result["routeSummary"][0])
        self.assertNotIn("totalProfitSoFar", result["iterations"][-1])

    def test_blocked_route_is_skipped(self):
        result = solve_transport_problem(
            {
                "mode": "transport",
                "supplierCount": 2,
                "receiverCount": 2,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2"],
                "supply": [10, 10],
                "demand": [10, 10],
                "costs": [[2, 3], [4, 5]],
                "blocked": [[True, False], [False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["allocations"][0][0], 0)
        self.assertEqual(result["allocations"][0][1], 10)
        self.assertEqual(result["allocations"][1][0], 10)

    def test_blocked_routes_avoid_greedy_dead_end(self):
        result = solve_transport_problem(
            {
                "mode": "transport",
                "supplierCount": 2,
                "receiverCount": 2,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2"],
                "supply": [5, 5],
                "demand": [5, 5],
                "costs": [[2, 3], [4, 5]],
                "blocked": [[False, False], [False, True]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["allocations"], [[0, 5], [5, 0]])

    def test_intermediary_uses_cheapest_available_path(self):
        result = solve_transport_problem(
            {
                "mode": "intermediary",
                "supplierCount": 1,
                "receiverCount": 1,
                "intermediaryCount": 2,
                "supplierNames": ["D1"],
                "receiverNames": ["O1"],
                "intermediaryNames": ["P1", "P2"],
                "supply": [12],
                "demand": [12],
                "supplierToIntermediaryCosts": [[6, 2]],
                "supplierToIntermediaryBlocked": [[False, False]],
                "intermediaryToReceiverCosts": [[1], [5]],
                "intermediaryToReceiverBlocked": [[False], [False]],
                "revenues": [[12]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["paths"][0][0]["intermediaryName"], "P1")
        self.assertEqual(result["totalCost"], 84)
        self.assertEqual(result["totalRevenue"], 144)
        self.assertEqual(result["totalProfit"], 60)

    def test_infeasible_when_all_routes_blocked(self):
        result = solve_transport_problem(
            {
                "mode": "transport",
                "supplierCount": 1,
                "receiverCount": 1,
                "supply": [5],
                "demand": [5],
                "costs": [[1]],
                "blocked": [[True]],
            }
        )

        self.assertFalse(result["success"])
        self.assertIn("Blokady", result["message"])


if __name__ == "__main__":
    unittest.main()
