from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Any

EPS = 1e-9
INF = 10**12
MAX_SIZE = 10


class SolverError(ValueError):
    """Input data cannot form a valid transport task."""


class _FlowEdge:
    def __init__(self, to_node: int, reverse_index: int, capacity: float, cost: float) -> None:
        self.to_node = to_node
        self.reverse_index = reverse_index
        self.capacity = capacity
        self.initial_capacity = capacity
        self.cost = cost


def _as_float(value: Any, field: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SolverError(f"Pole '{field}' musi byc liczba.") from exc
    if number < -EPS:
        raise SolverError(f"Pole '{field}' nie moze byc ujemne.")
    return 0.0 if abs(number) < EPS else number


def _format_number(value: float) -> float | int:
    if abs(value - round(value)) < EPS:
        return int(round(value))
    return round(value, 4)


def _normalize_names(values: list[Any], prefix: str, expected: int) -> list[str]:
    names: list[str] = []
    for index in range(expected):
        raw = values[index] if index < len(values) else ""
        name = str(raw).strip()
        names.append(name or f"{prefix}{index + 1}")
    return names


def _matrix(
    values: list[list[Any]],
    rows: int,
    cols: int,
    field: str,
    default: float = 0.0,
) -> list[list[float]]:
    result: list[list[float]] = []
    for row in range(rows):
        source_row = values[row] if row < len(values) and isinstance(values[row], list) else []
        out_row: list[float] = []
        for col in range(cols):
            raw = source_row[col] if col < len(source_row) else default
            out_row.append(_as_float(raw, f"{field}[{row + 1}][{col + 1}]"))
        result.append(out_row)
    return result


def _bool_matrix(values: list[list[Any]], rows: int, cols: int) -> list[list[bool]]:
    result: list[list[bool]] = []
    for row in range(rows):
        source_row = values[row] if row < len(values) and isinstance(values[row], list) else []
        result.append([bool(source_row[col]) if col < len(source_row) else False for col in range(cols)])
    return result


def _vector(values: list[Any], expected: int, field: str) -> list[float]:
    if expected < 1 or expected > MAX_SIZE:
        raise SolverError(f"Liczba elementow w '{field}' musi byc od 1 do {MAX_SIZE}.")
    return [_as_float(values[index] if index < len(values) else 0, f"{field}[{index + 1}]") for index in range(expected)]


def _validate_positive_total(values: list[float], field: str) -> None:
    if sum(values) <= EPS:
        raise SolverError(f"Suma w '{field}' musi byc wieksza od zera.")


def _clone_numeric_matrix(values: list[list[float]]) -> list[list[float | int]]:
    return [[_format_number(cell) for cell in row] for row in values]


def _clone_vector(values: list[float]) -> list[float | int]:
    return [_format_number(value) for value in values]


def solve_transport_problem(payload: dict[str, Any]) -> dict[str, Any]:
    mode = payload.get("mode", "transport")
    if mode not in {"transport", "intermediary"}:
        raise SolverError("Tryb musi miec wartosc 'transport' albo 'intermediary'.")

    supplier_count = int(payload.get("supplierCount") or len(payload.get("supply", [])) or 1)
    receiver_count = int(payload.get("receiverCount") or len(payload.get("demand", [])) or 1)
    if not 1 <= supplier_count <= MAX_SIZE or not 1 <= receiver_count <= MAX_SIZE:
        raise SolverError(f"Liczba dostawcow i odbiorcow musi byc od 1 do {MAX_SIZE}.")

    supplier_names = _normalize_names(payload.get("supplierNames", []), "D", supplier_count)
    receiver_names = _normalize_names(payload.get("receiverNames", []), "O", receiver_count)
    supply = _vector(payload.get("supply", []), supplier_count, "podaz")
    demand = _vector(payload.get("demand", []), receiver_count, "popyt")
    _validate_positive_total(supply, "podaz")
    _validate_positive_total(demand, "popyt")
    profit_enabled = payload.get("calculateProfit", True) is not False
    force_receiver_demand = mode == "intermediary" and profit_enabled and payload.get("forceReceiverDemand") is True
    required_receiver_index: int | None = None
    if force_receiver_demand:
        try:
            required_receiver_index = int(payload.get("requiredReceiverIndex", receiver_count - 1))
        except (TypeError, ValueError) as exc:
            raise SolverError("Wybrany odbiorca do wymuszenia popytu jest niepoprawny.") from exc
        if required_receiver_index < 0 or required_receiver_index >= receiver_count:
            raise SolverError("Wybrany odbiorca do wymuszenia popytu jest poza zakresem.")

    if mode == "transport":
        revenue_payload = payload.get("revenues", []) if profit_enabled else []
        revenues = _matrix(revenue_payload, supplier_count, receiver_count, "przychod", 0.0)
        costs = _matrix(payload.get("costs", []), supplier_count, receiver_count, "koszt", 0.0)
        blocked = _bool_matrix(payload.get("blocked", []), supplier_count, receiver_count)
        path_matrix = [
            [
                {
                    "type": "direct",
                    "label": f"{supplier_names[i]} -> {receiver_names[j]}",
                    "cost": costs[i][j],
                }
                for j in range(receiver_count)
            ]
            for i in range(supplier_count)
        ]
        intermediary_names: list[str] = []
        segment_data: dict[str, Any] = {}
    else:
        purchase_costs = _vector(payload.get("purchaseCosts", []), supplier_count, "koszt_zakupu")
        sale_prices = _vector(payload.get("salePrices", []), receiver_count, "cena_sprzedazy")
        transport_costs = _matrix(payload.get("costs", []), supplier_count, receiver_count, "koszt_transportu", 0.0)
        blocked = _bool_matrix(payload.get("blocked", []), supplier_count, receiver_count)
        costs = [
            [purchase_costs[i] + transport_costs[i][j] for j in range(receiver_count)]
            for i in range(supplier_count)
        ]
        revenues = [[sale_prices[j] for j in range(receiver_count)] for _ in range(supplier_count)]
        path_matrix = [
            [
                {
                    "type": "intermediary",
                    "label": f"{supplier_names[i]} -> {receiver_names[j]}",
                    "purchaseCost": _format_number(purchase_costs[i]),
                    "transportCost": _format_number(transport_costs[i][j]),
                    "salePrice": _format_number(sale_prices[j]),
                    "cost": _format_number(costs[i][j]),
                    "unitProfit": _format_number(revenues[i][j] - costs[i][j]),
                }
                for j in range(receiver_count)
            ]
            for i in range(supplier_count)
        ]
        intermediary_names = []
        segment_data = {
            "purchaseCosts": _clone_vector(purchase_costs),
            "salePrices": _clone_vector(sale_prices),
            "transportCosts": _clone_numeric_matrix(transport_costs),
        }

    if mode == "intermediary" and profit_enabled:
        balanced = _open_profit_status(supply, demand)
        solution = _maximum_profit_with_blocks(
            supply,
            demand,
            costs,
            revenues,
            blocked,
            path_matrix,
            required_receiver_index,
        )
    else:
        balanced = _balance_problem(
            supply,
            demand,
            supplier_names,
            receiver_names,
            costs,
            revenues,
            blocked,
            path_matrix,
            mode,
        )
        solution = _northwest_corner_with_blocks(supply, demand, costs, revenues, blocked, path_matrix, profit_enabled)

    route_summary = _route_summary(
        solution["allocations"],
        costs,
        revenues,
        profit_enabled,
        supplier_names,
        receiver_names,
        path_matrix,
    )

    return {
        "success": solution["success"],
        "mode": mode,
        "message": solution["message"],
        "warnings": balanced["warnings"] + solution["warnings"],
        "balanced": balanced,
        "profitEnabled": profit_enabled,
        "supplierNames": supplier_names,
        "receiverNames": receiver_names,
        "intermediaryNames": intermediary_names,
        "supply": _clone_vector(supply),
        "demand": _clone_vector(demand),
        "costs": _clone_numeric_matrix(costs),
        "revenues": _clone_numeric_matrix(revenues),
        "unitProfits": _clone_numeric_matrix(_profit_matrix(costs, revenues)) if profit_enabled else None,
        "blocked": blocked,
        "paths": path_matrix,
        "segments": segment_data,
        "forceReceiverDemand": force_receiver_demand,
        "requiredReceiverIndex": required_receiver_index,
        "iterations": solution["iterations"],
        "allocations": _clone_numeric_matrix(solution["allocations"]),
        "totalCost": _format_number(solution["total_cost"]),
        "totalRevenue": _format_number(solution["total_revenue"]) if profit_enabled else None,
        "totalProfit": _format_number(solution["total_profit"]) if profit_enabled else None,
        "routeSummary": route_summary,
    }


def _balance_problem(
    supply: list[float],
    demand: list[float],
    supplier_names: list[str],
    receiver_names: list[str],
    costs: list[list[float]],
    revenues: list[list[float]],
    blocked: list[list[bool]],
    paths: list[list[dict[str, Any]]],
    mode: str,
) -> dict[str, Any]:
    total_supply = sum(supply)
    total_demand = sum(demand)
    warnings: list[str] = []
    added: dict[str, Any] | None = None

    if abs(total_supply - total_demand) <= EPS:
        return {
            "wasBalanced": True,
            "added": None,
            "warnings": warnings,
            "totalSupply": _format_number(total_supply),
            "totalDemand": _format_number(total_demand),
        }

    if total_supply > total_demand:
        missing = total_supply - total_demand
        receiver_names.append("Odbiorca fikcyjny")
        demand.append(missing)
        for supplier_index, row in enumerate(costs):
            row.append(0.0)
            revenues[supplier_index].append(0.0)
            blocked[supplier_index].append(False)
            paths[supplier_index].append(
                {
                    "type": "dummy",
                    "label": f"{supplier_names[supplier_index]} -> Odbiorca fikcyjny",
                    "cost": 0,
                }
            )
        added = {"type": "receiver", "name": "Odbiorca fikcyjny", "amount": _format_number(missing)}
        warnings.append("Dodano odbiorce fikcyjnego, aby zbilansowac nadwyzke podazy.")
    else:
        missing = total_demand - total_supply
        supplier_names.append("Dostawca fikcyjny")
        supply.append(missing)
        costs.append([0.0 for _ in demand])
        revenues.append([0.0 for _ in demand])
        blocked.append([False for _ in demand])
        paths.append(
            [
                {
                    "type": "dummy",
                    "label": f"Dostawca fikcyjny -> {receiver_name}",
                    "cost": 0,
                }
                for receiver_name in receiver_names
            ]
        )
        added = {"type": "supplier", "name": "Dostawca fikcyjny", "amount": _format_number(missing)}
        warnings.append("Dodano dostawce fikcyjnego, aby zbilansowac nadwyzke popytu.")

    return {
        "wasBalanced": False,
        "added": added,
        "warnings": warnings,
        "totalSupply": _format_number(sum(supply)),
        "totalDemand": _format_number(sum(demand)),
        "mode": mode,
    }


def _open_profit_status(supply: list[float], demand: list[float]) -> dict[str, Any]:
    return {
        "wasBalanced": abs(sum(supply) - sum(demand)) <= EPS,
        "added": None,
        "warnings": [],
        "totalSupply": _format_number(sum(supply)),
        "totalDemand": _format_number(sum(demand)),
        "mode": "intermediary",
    }


def _maximum_profit_with_blocks(
    supply: list[float],
    demand: list[float],
    costs: list[list[float]],
    revenues: list[list[float]],
    blocked: list[list[bool]],
    paths: list[list[dict[str, Any]]],
    required_receiver_index: int | None = None,
) -> dict[str, Any]:
    rows = len(supply)
    cols = len(demand)
    unit_profits = _profit_matrix(costs, revenues)
    allocations = _optimized_profit_allocations(supply, demand, unit_profits, blocked, required_receiver_index)
    if required_receiver_index is not None:
        required_amount = sum(allocations[row][required_receiver_index] for row in range(rows))
        if required_amount + EPS < demand[required_receiver_index]:
            return {
                "success": False,
                "message": "Nie da sie zaspokoic pelnego popytu wybranego odbiorcy przy obecnych blokadach i podazy.",
                "warnings": [],
                "iterations": [],
                "allocations": allocations,
                "total_cost": _total_cost(allocations, costs),
                "total_revenue": _total_revenue(allocations, revenues),
                "total_profit": _total_profit(allocations, costs, revenues),
            }

    remaining_supply = [
        max(0.0, supply[row] - sum(allocations[row][col] for col in range(cols)))
        for row in range(rows)
    ]
    remaining_demand = [
        max(0.0, demand[col] - sum(allocations[row][col] for row in range(rows)))
        for col in range(cols)
    ]
    iterations = _iterations_from_allocations(supply, demand, allocations, costs, revenues, paths)

    warnings: list[str] = []
    if sum(remaining_supply) > EPS:
        warnings.append("Czesc podazy zostala niewykorzystana, bo pozostale trasy nie zwiekszaja zysku.")
    if sum(remaining_demand) > EPS:
        warnings.append("Czesc popytu pozostala niezaspokojona w planie maksymalizacji zysku.")
    if required_receiver_index is not None:
        forced_negative = any(
            allocations[row][required_receiver_index] > EPS
            and unit_profits[row][required_receiver_index] < -EPS
            for row in range(rows)
        )
        if forced_negative:
            warnings.append("Wymuszony popyt odbiorcy wymagal uzycia trasy z ujemnym zyskiem jednostkowym.")

    return {
        "success": True,
        "message": (
            "Plan dostaw wyznaczony metoda maksymalizacji zysku z wymuszonym popytem odbiorcy."
            if required_receiver_index is not None
            else "Plan dostaw wyznaczony metoda maksymalizacji zysku."
        ),
        "warnings": warnings,
        "iterations": iterations,
        "allocations": allocations,
        "total_cost": _total_cost(allocations, costs),
        "total_revenue": _total_revenue(allocations, revenues),
        "total_profit": _total_profit(allocations, costs, revenues),
    }


def _optimized_profit_allocations(
    supply: list[float],
    demand: list[float],
    unit_profits: list[list[float]],
    blocked: list[list[bool]],
    required_receiver_index: int | None,
) -> list[list[float]]:
    rows = len(supply)
    cols = len(demand)
    total_supply = sum(supply)
    if total_supply <= EPS:
        return [[0.0 for _ in range(cols)] for _ in range(rows)]

    max_abs_profit = max(
        [abs(unit_profits[row][col]) for row in range(rows) for col in range(cols)] + [1.0]
    )
    required_bonus = (max_abs_profit + 1.0) * (total_supply + sum(demand) + 1.0)

    source = 0
    supplier_offset = 1
    receiver_offset = supplier_offset + rows
    dummy_receiver = receiver_offset + cols
    sink = dummy_receiver + 1
    graph: list[list[_FlowEdge]] = [[] for _ in range(sink + 1)]
    route_edges: dict[tuple[int, int], _FlowEdge] = {}

    for row, amount in enumerate(supply):
        _add_flow_edge(graph, source, supplier_offset + row, amount, 0.0)

    for row in range(rows):
        for col in range(cols):
            if blocked[row][col]:
                continue
            is_required_receiver = required_receiver_index is not None and col == required_receiver_index
            if not is_required_receiver and unit_profits[row][col] <= EPS:
                continue
            adjusted_profit = unit_profits[row][col]
            if is_required_receiver:
                adjusted_profit += required_bonus
            route_edges[(row, col)] = _add_flow_edge(
                graph,
                supplier_offset + row,
                receiver_offset + col,
                INF,
                -adjusted_profit,
            )
        _add_flow_edge(graph, supplier_offset + row, dummy_receiver, INF, 0.0)

    for col, amount in enumerate(demand):
        _add_flow_edge(graph, receiver_offset + col, sink, amount, 0.0)
    _add_flow_edge(graph, dummy_receiver, sink, total_supply, 0.0)

    _min_cost_flow(graph, source, sink, total_supply)

    allocations = [[0.0 for _ in range(cols)] for _ in range(rows)]
    for (row, col), edge in route_edges.items():
        flow = edge.initial_capacity - edge.capacity
        allocations[row][col] = 0.0 if abs(flow) < EPS else flow
    return allocations


def _add_flow_edge(
    graph: list[list[_FlowEdge]],
    from_node: int,
    to_node: int,
    capacity: float,
    cost: float,
) -> _FlowEdge:
    forward = _FlowEdge(to_node, len(graph[to_node]), capacity, cost)
    reverse = _FlowEdge(from_node, len(graph[from_node]), 0.0, -cost)
    graph[from_node].append(forward)
    graph[to_node].append(reverse)
    return forward


def _min_cost_flow(graph: list[list[_FlowEdge]], source: int, sink: int, amount: float) -> None:
    remaining = amount
    node_count = len(graph)

    while remaining > EPS:
        distances = [float("inf") for _ in range(node_count)]
        parent_node = [-1 for _ in range(node_count)]
        parent_edge = [-1 for _ in range(node_count)]
        in_queue = [False for _ in range(node_count)]

        distances[source] = 0.0
        queue: deque[int] = deque([source])
        in_queue[source] = True

        while queue:
            node = queue.popleft()
            in_queue[node] = False
            for edge_index, edge in enumerate(graph[node]):
                if edge.capacity <= EPS:
                    continue
                next_cost = distances[node] + edge.cost
                if next_cost + EPS < distances[edge.to_node]:
                    distances[edge.to_node] = next_cost
                    parent_node[edge.to_node] = node
                    parent_edge[edge.to_node] = edge_index
                    if not in_queue[edge.to_node]:
                        queue.append(edge.to_node)
                        in_queue[edge.to_node] = True

        if parent_node[sink] == -1:
            return

        flow = remaining
        node = sink
        while node != source:
            edge = graph[parent_node[node]][parent_edge[node]]
            flow = min(flow, edge.capacity)
            node = parent_node[node]

        node = sink
        while node != source:
            edge = graph[parent_node[node]][parent_edge[node]]
            edge.capacity -= flow
            graph[edge.to_node][edge.reverse_index].capacity += flow
            node = parent_node[node]
        remaining -= flow


def _iterations_from_allocations(
    supply: list[float],
    demand: list[float],
    allocations: list[list[float]],
    costs: list[list[float]],
    revenues: list[list[float]],
    paths: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    rows = len(supply)
    cols = len(demand)
    remaining_supply = supply[:]
    remaining_demand = demand[:]
    running_allocations = [[0.0 for _ in range(cols)] for _ in range(rows)]
    iterations: list[dict[str, Any]] = []
    step = 1

    for row in range(rows):
        for col in range(cols):
            amount = allocations[row][col]
            if amount <= EPS:
                continue
            supply_before = remaining_supply[:]
            demand_before = remaining_demand[:]
            remaining_supply[row] = max(0.0, remaining_supply[row] - amount)
            remaining_demand[col] = max(0.0, remaining_demand[col] - amount)
            running_allocations[row][col] += amount
            unit_profit = revenues[row][col] - costs[row][col]

            iterations.append(
                {
                    "step": step,
                    "supplierIndex": row,
                    "receiverIndex": col,
                    "amount": _format_number(amount),
                    "unitCost": _format_number(costs[row][col]),
                    "unitRevenue": _format_number(revenues[row][col]),
                    "unitProfit": _format_number(unit_profit),
                    "stepCost": _format_number(amount * costs[row][col]),
                    "stepRevenue": _format_number(amount * revenues[row][col]),
                    "stepProfit": _format_number(amount * unit_profit),
                    "path": deepcopy(paths[row][col]),
                    "supplyBefore": _clone_vector(supply_before),
                    "demandBefore": _clone_vector(demand_before),
                    "supplyAfter": _clone_vector(remaining_supply),
                    "demandAfter": _clone_vector(remaining_demand),
                    "allocations": _clone_numeric_matrix(running_allocations),
                    "totalCostSoFar": _format_number(_total_cost(running_allocations, costs)),
                    "totalRevenueSoFar": _format_number(_total_revenue(running_allocations, revenues)),
                    "totalProfitSoFar": _format_number(_total_profit(running_allocations, costs, revenues)),
                    "warning": "",
                }
            )
            step += 1

    return iterations


def _northwest_corner_with_blocks(
    supply: list[float],
    demand: list[float],
    costs: list[list[float]],
    revenues: list[list[float]],
    blocked: list[list[bool]],
    paths: list[list[dict[str, Any]]],
    profit_enabled: bool,
) -> dict[str, Any]:
    rows = len(supply)
    cols = len(demand)
    remaining_supply = supply[:]
    remaining_demand = demand[:]
    allocations = [[0.0 for _ in range(cols)] for _ in range(rows)]
    iterations: list[dict[str, Any]] = []
    warnings: list[str] = []
    step = 1

    if not _has_feasible_flow(remaining_supply, remaining_demand, blocked):
        return {
            "success": False,
            "message": "Blokady tras uniemozliwiaja zbilansowanie wszystkich dostaw.",
            "warnings": warnings,
            "iterations": iterations,
            "allocations": allocations,
            "total_cost": 0.0,
            "total_revenue": 0.0 if profit_enabled else None,
            "total_profit": 0.0 if profit_enabled else None,
        }

    while sum(remaining_demand) > EPS:
        candidate = _find_northwest_candidate(remaining_supply, remaining_demand, blocked)
        if candidate is None:
            return {
                "success": False,
                "message": "Brak dostepnej trasy dla pozostalej podazy i popytu.",
                "warnings": warnings,
                "iterations": iterations,
                "allocations": allocations,
                "total_cost": _total_cost(allocations, costs),
                "total_revenue": _total_revenue(allocations, revenues) if profit_enabled else None,
                "total_profit": _total_profit(allocations, costs, revenues) if profit_enabled else None,
            }

        supplier_index, receiver_index, skipped = candidate
        amount = min(remaining_supply[supplier_index], remaining_demand[receiver_index])
        supply_before = remaining_supply[:]
        demand_before = remaining_demand[:]

        remaining_supply[supplier_index] -= amount
        remaining_demand[receiver_index] -= amount
        if abs(remaining_supply[supplier_index]) < EPS:
            remaining_supply[supplier_index] = 0.0
        if abs(remaining_demand[receiver_index]) < EPS:
            remaining_demand[receiver_index] = 0.0
        allocations[supplier_index][receiver_index] += amount

        iteration_warning = ""
        if skipped:
            iteration_warning = "Pominieto zablokowane albo puste komorki przed tym przydzialem."

        iteration = {
            "step": step,
            "supplierIndex": supplier_index,
            "receiverIndex": receiver_index,
            "amount": _format_number(amount),
            "unitCost": _format_number(costs[supplier_index][receiver_index]),
            "stepCost": _format_number(amount * costs[supplier_index][receiver_index]),
            "path": deepcopy(paths[supplier_index][receiver_index]),
            "supplyBefore": _clone_vector(supply_before),
            "demandBefore": _clone_vector(demand_before),
            "supplyAfter": _clone_vector(remaining_supply),
            "demandAfter": _clone_vector(remaining_demand),
            "allocations": _clone_numeric_matrix(allocations),
            "totalCostSoFar": _format_number(_total_cost(allocations, costs)),
            "warning": iteration_warning,
        }
        if profit_enabled:
            iteration.update(
                {
                    "unitRevenue": _format_number(revenues[supplier_index][receiver_index]),
                    "unitProfit": _format_number(
                        revenues[supplier_index][receiver_index] - costs[supplier_index][receiver_index]
                    ),
                    "stepRevenue": _format_number(amount * revenues[supplier_index][receiver_index]),
                    "stepProfit": _format_number(
                        amount * (revenues[supplier_index][receiver_index] - costs[supplier_index][receiver_index])
                    ),
                    "totalRevenueSoFar": _format_number(_total_revenue(allocations, revenues)),
                    "totalProfitSoFar": _format_number(_total_profit(allocations, costs, revenues)),
                }
            )
        iterations.append(iteration)
        step += 1

    return {
        "success": True,
        "message": "Rozwiazanie poczatkowe wyznaczone metoda wierzcholka polnocno-zachodniego.",
        "warnings": warnings,
        "iterations": iterations,
        "allocations": allocations,
        "total_cost": _total_cost(allocations, costs),
        "total_revenue": _total_revenue(allocations, revenues) if profit_enabled else None,
        "total_profit": _total_profit(allocations, costs, revenues) if profit_enabled else None,
    }


def _find_northwest_candidate(
    remaining_supply: list[float],
    remaining_demand: list[float],
    blocked: list[list[bool]],
) -> tuple[int, int, int] | None:
    skipped = 0
    for row, supply in enumerate(remaining_supply):
        for col, demand in enumerate(remaining_demand):
            if supply <= EPS or demand <= EPS:
                skipped += 1
                continue
            if blocked[row][col]:
                skipped += 1
                continue
            amount = min(supply, demand)
            next_supply = remaining_supply[:]
            next_demand = remaining_demand[:]
            next_supply[row] -= amount
            next_demand[col] -= amount
            if _has_feasible_flow(next_supply, next_demand, blocked):
                return row, col, skipped
            skipped += 1
    return None


def _total_cost(allocations: list[list[float]], costs: list[list[float]]) -> float:
    return sum(allocations[row][col] * costs[row][col] for row in range(len(allocations)) for col in range(len(costs[row])))


def _total_revenue(allocations: list[list[float]], revenues: list[list[float]]) -> float:
    return sum(
        allocations[row][col] * revenues[row][col]
        for row in range(len(allocations))
        for col in range(len(revenues[row]))
    )


def _profit_matrix(costs: list[list[float]], revenues: list[list[float]]) -> list[list[float]]:
    return [
        [revenues[row][col] - costs[row][col] for col in range(len(costs[row]))]
        for row in range(len(costs))
    ]


def _total_profit(allocations: list[list[float]], costs: list[list[float]], revenues: list[list[float]]) -> float:
    return _total_revenue(allocations, revenues) - _total_cost(allocations, costs)


def _route_summary(
    allocations: list[list[float]],
    costs: list[list[float]],
    revenues: list[list[float]],
    profit_enabled: bool,
    supplier_names: list[str],
    receiver_names: list[str],
    paths: list[list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for row, allocation_row in enumerate(allocations):
        for col, amount in enumerate(allocation_row):
            if amount <= EPS:
                continue
            unit_cost = costs[row][col]
            unit_revenue = revenues[row][col]
            item = {
                "supplier": supplier_names[row],
                "receiver": receiver_names[col],
                "amount": _format_number(amount),
                "unitCost": _format_number(unit_cost),
                "cost": _format_number(amount * unit_cost),
                "path": deepcopy(paths[row][col]),
            }
            if profit_enabled:
                item.update(
                    {
                        "unitRevenue": _format_number(unit_revenue),
                        "unitProfit": _format_number(unit_revenue - unit_cost),
                        "revenue": _format_number(amount * unit_revenue),
                        "profit": _format_number(amount * (unit_revenue - unit_cost)),
                    }
                )
            summary.append(item)
    return summary


def _has_feasible_flow(supply: list[float], demand: list[float], blocked: list[list[bool]]) -> bool:
    rows = len(supply)
    cols = len(demand)
    node_count = 2 + rows + cols
    source = 0
    sink = node_count - 1
    graph = [[0.0 for _ in range(node_count)] for _ in range(node_count)]

    for row, amount in enumerate(supply):
        graph[source][1 + row] = amount
    for row in range(rows):
        for col in range(cols):
            if not blocked[row][col]:
                graph[1 + row][1 + rows + col] = INF
    for col, amount in enumerate(demand):
        graph[1 + rows + col][sink] = amount

    max_flow = 0.0
    while True:
        parent = [-1 for _ in range(node_count)]
        parent[source] = source
        queue: deque[int] = deque([source])
        while queue and parent[sink] == -1:
            current = queue.popleft()
            for neighbor, capacity in enumerate(graph[current]):
                if parent[neighbor] == -1 and capacity > EPS:
                    parent[neighbor] = current
                    queue.append(neighbor)
                    if neighbor == sink:
                        break
        if parent[sink] == -1:
            break
        flow = INF
        node = sink
        while node != source:
            prev = parent[node]
            flow = min(flow, graph[prev][node])
            node = prev
        node = sink
        while node != source:
            prev = parent[node]
            graph[prev][node] -= flow
            graph[node][prev] += flow
            node = prev
        max_flow += flow

    return abs(max_flow - sum(demand)) <= EPS
