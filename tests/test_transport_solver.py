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

    def test_intermediary_maximizes_profit_from_purchase_sale_and_transport(self):
        result = solve_transport_problem(
            {
                "mode": "intermediary",
                "supplierCount": 2,
                "receiverCount": 3,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2", "O3"],
                "supply": [20, 30],
                "demand": [10, 28, 27],
                "purchaseCosts": [10, 12],
                "salePrices": [30, 25, 30],
                "costs": [[8, 14, 17], [12, 9, 19]],
                "blocked": [[False, False, False], [False, False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["allocations"], [[10, 0, 10], [0, 28, 0]])
        self.assertEqual(result["totalCost"], 1038)
        self.assertEqual(result["totalRevenue"], 1300)
        self.assertEqual(result["totalProfit"], 262)
        self.assertEqual(result["unitProfits"], [[12, 1, 3], [6, 4, -1]])
        self.assertEqual(result["iterations"][0]["unitProfit"], 12)
        self.assertEqual(result["routeSummary"][0]["profit"], 120)

    def test_intermediary_respects_blocked_transport_routes(self):
        result = solve_transport_problem(
            {
                "mode": "intermediary",
                "supplierCount": 2,
                "receiverCount": 2,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2"],
                "supply": [10, 10],
                "demand": [10, 10],
                "purchaseCosts": [4, 4],
                "salePrices": [20, 20],
                "costs": [[1, 2], [9, 3]],
                "blocked": [[True, False], [False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["allocations"], [[0, 10], [10, 0]])

    def test_intermediary_can_force_full_demand_for_selected_receiver(self):
        result = solve_transport_problem(
            {
                "mode": "intermediary",
                "forceReceiverDemand": True,
                "requiredReceiverIndex": 2,
                "supplierCount": 2,
                "receiverCount": 3,
                "supplierNames": ["D1", "D2"],
                "receiverNames": ["O1", "O2", "O3"],
                "supply": [20, 30],
                "demand": [10, 28, 27],
                "purchaseCosts": [10, 12],
                "salePrices": [30, 25, 30],
                "costs": [[8, 14, 17], [12, 9, 19]],
                "blocked": [[False, False, False], [False, False, False]],
            }
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["allocations"], [[10, 0, 10], [0, 13, 17]])
        self.assertEqual(result["totalCost"], 1250)
        self.assertEqual(result["totalRevenue"], 1435)
        self.assertEqual(result["totalProfit"], 185)
        self.assertTrue(result["forceReceiverDemand"])
        self.assertEqual(result["requiredReceiverIndex"], 2)

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
