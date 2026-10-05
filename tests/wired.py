import time
import pygame
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roomba import Roomba

# ---- settings ----
SAFE_MODE = False        # False = Full mode (no cliff/wheel-drop protection!)
START_SPEED = 150        # mm/s
MAX_SPEED = 500
SPEED_STEP = 25
ARC_RADIUS = 300         # mm, used when turning while moving (W+A, W+D)
RESEND_INTERVAL = 0.1    # seconds, resend the current command so it can't get "lost"


def compute_command(keys, speed):
    """Turn the held keys into (velocity, radius). radius None = straight."""
    fwd = int(keys[pygame.K_w]) - int(keys[pygame.K_s])      # +1 forward, -1 back
    turn = int(keys[pygame.K_a]) - int(keys[pygame.K_d])     # +1 left, -1 right

    if fwd == 0 and turn == 0:
        return (0, None)

    if fwd == 0:
        # spin in place: radius 1 = counter-clockwise, -1 = clockwise
        return (speed, 1 if turn > 0 else -1)

    velocity = fwd * speed
    if turn == 0:
        return (velocity, None)
    return (velocity, ARC_RADIUS if turn > 0 else -ARC_RADIUS)


def describe(cmd):
    velocity, radius = cmd
    if velocity == 0:
        return "STOPPED"
    if radius is None:
        return "FORWARD" if velocity > 0 else "REVERSE"
    if radius in (1, -1):
        return "SPIN LEFT" if radius == 1 else "SPIN RIGHT"
    return "ARC LEFT" if radius > 0 else "ARC RIGHT"


def main():
    roomba = Roomba()
    roomba.connect_serial(attempts=1)

    if not (roomba.ser and roomba.ser.is_open):
        print("Could not open the serial port, exiting.")
        return

    roomba.start_roomba(safe_mode=SAFE_MODE)
    roomba.set_led(255)

    pygame.init()
    screen = pygame.display.set_mode((460, 260))
    pygame.display.set_caption("Roomba control")
    font = pygame.font.SysFont("consolas", 22)
    small = pygame.font.SysFont("consolas", 16)
    clock = pygame.time.Clock()

    speed = START_SPEED
    last_cmd = None
    last_send = 0.0
    running = True

    try:
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key in (pygame.K_UP, pygame.K_e):
                        speed = min(MAX_SPEED, speed + SPEED_STEP)
                    elif event.key in (pygame.K_DOWN, pygame.K_q):
                        speed = max(SPEED_STEP, speed - SPEED_STEP)

            keys = pygame.key.get_pressed()
            cmd = (0, None) if keys[pygame.K_SPACE] else compute_command(keys, speed)

            # send on change, plus a periodic resend
            now = time.time()
            if cmd != last_cmd or now - last_send >= RESEND_INTERVAL:
                roomba.drive(*cmd)
                last_cmd = cmd
                last_send = now

            # ---- draw ----
            screen.fill((20, 20, 24))
            lines = [
                (font, f"State: {describe(cmd)}", (255, 255, 255)),
                (font, f"Speed: {speed} mm/s", (120, 220, 140)),
                (small, "W/S  forward / reverse", (170, 170, 170)),
                (small, "A/D  turn left / right (W+A for arcs)", (170, 170, 170)),
                (small, "Q/E or Down/Up  speed - / +", (170, 170, 170)),
                (small, "SPACE  emergency stop", (170, 170, 170)),
                (small, "ESC  quit", (170, 170, 170)),
            ]
            y = 20
            for f, text, color in lines:
                screen.blit(f.render(text, True, color), (20, y))
                y += 36 if f is font else 28
            pygame.display.flip()

            clock.tick(60)
    finally:
        # always stop the wheels, even on a crash or Ctrl+C
        try:
            roomba.drive(0)
        finally:
            roomba.stop_roomba()
            pygame.quit()


if __name__ == "__main__":
    main()