"""
GUIDE: Using cProfile for frame profiling

There are several ways to use cProfile:

METHOD 1: Command-line profiling (easiest, run on existing module)
    python -m cProfile -s cumulative main.py
    # -s cumulative: sort by cumulative time
    # -s time: sort by time in function only

METHOD 2: Using cProfile directly (what profile_frame.py does)
    - Import cProfile
    - Create profiler with cProfile.Profile()
    - Call profiler.enable() before code block
    - Call profiler.disable() after code block
    - Use pstats.Stats to analyze

METHOD 3: Quick inline profiling
    - Wrap function call in profiler: profiler.runcall(game.update, dt)
    - Good for profiling specific functions only

KEY STATS METRICS:
    ncalls:     Number of function calls
    tottime:    Total time in function (excluding sub-function calls)
    cumtime:    Cumulative time (including sub-function calls)
    
SORTING OPTIONS (for pstats.Stats.sort_stats()):
    'cumulative' - Cumulative time spent in function (slowest overall)
    'time'       - Internal time only, excludes sub-calls (slowest internally)
    'calls'      - Number of function calls (most called)
    'name'       - Alphabetically

USAGE EXAMPLES:
    # Profile and sort by cumulative time
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Show top 20
    
    # Print only specific functions
    stats.print_callers('pathfinding')
    stats.print_callees('pathfinding')
    
    # Restrict output
    stats.print_stats('pathfinding')  # Only functions with 'pathfinding' in name
"""

# Quick test - run with: python profile_reference.py
if __name__ == "__main__":
    import cProfile
    import pstats
    
    def example_function(n):
        total = 0
        for i in range(n):
            total += i
        return total
    
    profiler = cProfile.Profile()
    profiler.enable()
    
    result = example_function(1000000)
    
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('time')
    stats.print_stats()
