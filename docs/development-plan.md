# Incremental development plan

The project is built in small, independently testable slices:

1. Establish the Python package, mandatory Makefile targets, quality configuration,
   command-line entry point, and test harness.
2. Add typed domain entities for zones, links, drones, and the graph.
3. Build the strict map parser with line-aware diagnostics and reachability reporting.
4. Add route discovery and a capacity-aware scheduler, then test it on simple maps.
5. Implement atomic turn simulation, including restricted-zone transit and same-turn
   capacity release.
6. Keep the official output separate from terminal visualization.
7. Benchmark all provided maps, improve general scheduling decisions, and document
   measured results.

The scheduler will use graph traversal implemented locally (no graph libraries), route
selection based on travel time and priority, and reservations that are validated against
the state at the beginning of each turn.
