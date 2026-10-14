*This project has been created as part of the 42 curriculum by icaldas-.*

# Fly-in

## Description

Fly-in routes a fleet of drones from one start hub to one end hub in a constrained,
bidirectional zone graph. It parses the subject map format, rejects malformed maps with
line-aware diagnostics, and simulates simultaneous turns while respecting zone and link
capacities. A valid but disconnected map is reported separately as unsolvable.

## Instructions

Python 3.10 or newer is required (the project only uses the standard library at runtime).

```sh
make run MAP=path/to/map.txt
make run MAP=path/to/map.txt ARGS=--visual
make test
make lint
make lint-strict
```

`--visual` writes an ANSI-colored, turn-by-turn view to standard error. It includes each
movement, the post-turn occupants of every zone, and drones crossing restricted
connections. Standard output remains the mandatory movement-only format. Development
tools can be installed with `make install`.

Example map:

```text
nb_drones: 1
start_hub: start 0 0 [color=green]
end_hub: goal 1 0 [color=red]
connection: start-goal
```

Expected output:

```text
D1-goal
```

## Architecture and algorithms

- `domain.py` contains object-oriented `Zone`, `Connection`, `Drone`, and `Graph`
  models, including their invariants.
- `parser.py` implements the strict map grammar and wraps diagnostics in `ParseError`.
- `routing.py` uses a local reverse Dijkstra traversal (no graph library) to cache the
  least remaining travel cost to the end. Blocked zones are excluded; restricted-zone
  arrival costs are two turns; priority zones break equal-cost ties.
- `simulation.py` makes every turn from the state at its start. It subtracts all selected
  departures before checking arrivals, so capacity freed during a turn can be reused in
  that turn. A restricted arrival occupies its connection for one turn and is forced to
  arrive on the next turn. Equal-cost next hops are round-robin distributed by drone ID.
- `visualization.py` keeps optional human feedback on standard error, preserving the
  evaluator-facing output on standard output.

Dijkstra costs `O((V + E) log V)` time and `O(V)` additional space. Each simulated turn
uses `O(D + V + E)` space and time in the current capacity-validation scheduler, where
`D` is the drone count.

## Visual representation

The `--visual` mode renders every turn on standard error. Movements and zone names use
their configured ANSI terminal colors; the view then lists the drones occupying each zone
and any drone in transit to a restricted zone. It is intentionally separate from standard
output, so it cannot corrupt the official line-by-line simulation format.

## Benchmarks

Measured locally against the supplied maps after the current implementation:

| Map | Turns | Subject optimum |
| --- | ---: | ---: |
| Linear path | 4 | 4 |
| Simple fork | 4 | 4 |
| Basic capacity | 4 | 4 |
| Dead end trap | 8 | 8 |
| Circular loop | 15 | 10 |
| Priority puzzle | 8 | 6 |
| Maze nightmare | 13 | 13 |
| Capacity hell | 16 | 16 |
| Ultimate challenge | 26 | 26 |
| The Impossible Dream (optional) | 43 | 43 |

The circular and priority maps are known optimization opportunities. They complete with a
valid schedule but are not currently within 25% of their targets.

## Resources

- [Python `heapq` documentation](https://docs.python.org/3/library/heapq.html)
- [Dijkstra's algorithm](https://en.wikipedia.org/wiki/Dijkstra%27s_algorithm)
- The official Fly-in subject supplied with this repository

AI was used as a collaborative engineering aid to inspect the subject, propose and review
the implementation structure, write code and tests, and run quality checks. All generated
code was reviewed, executed, and incrementally committed during development.
