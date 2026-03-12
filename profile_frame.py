"""
Profile a single frame using cProfile.
This helps identify which functions consume the most time in one game frame.
"""

import cProfile
import pstats
import io
from game_state_manager import GameStateManager


def profile_single_frame():
    """Run a single frame and profile its execution."""
    
    # Initialize game
    game = GameStateManager()
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Let the game settle for a few frames
    for _ in range(5):
        dt = 1 / 60  # Assume 60 FPS
        game.handle_events()
        game.update(dt)
        game.draw(game.clock.get_fps())
    
    # Profile the next frame
    dt = 1 / 60
    profiler.enable()
    
    game.handle_events()
    game.update(dt)
    game.draw(game.clock.get_fps())
    
    profiler.disable()
    
    # Print results
    print("\n" + "="*80)
    print("FRAME PROFILING RESULTS - Cumulative Time (sorted by time spent)")
    print("="*80 + "\n")
    
    stats = pstats.Stats(profiler, stream=io.StringIO())
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 functions
    print(stats.stream.getvalue())
    
    print("\n" + "="*80)
    print("FRAME PROFILING RESULTS - Internal Time (sorted by time in function only)")
    print("="*80 + "\n")
    
    stats = pstats.Stats(profiler, stream=io.StringIO())
    stats.sort_stats('time')
    stats.print_stats(20)  # Top 20 functions
    print(stats.stream.getvalue())


if __name__ == "__main__":
    profile_single_frame()
    import pygame
    pygame.quit()
