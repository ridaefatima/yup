import socket
import asyncio
import websockets
import pygame

DEADZONE = 0.1

# Rover details
ROVER_IP = '127.0.0.1'  # Replace with the actual IP ADDRESS of rover
ROVER_PORT = 12345  # Replace with the actual PORT of rover

# Initialize socket
rover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Initialize previous PWM values for comparison
prev_left_wheel_pwm = None
prev_right_wheel_pwm = None
prev_arm_pwm = None

def create_drive_packet(right_wheel_pwms, left_wheel_pwms):
    """Create a packet for driving commands."""
    return f"D_{right_wheel_pwms[0]}_{right_wheel_pwms[1]}_{right_wheel_pwms[2]}_{left_wheel_pwms[0]}_{left_wheel_pwms[1]}_{left_wheel_pwms[2]}"

def create_arm_packet(shoulder_pwm, wristright_pwm, wristleft_pwm, claw_pwm, gantry_pwm, elbow_pwm):
    """Create a packet for arm commands."""
    return f"A_{elbow_pwm}_{wristright_pwm}_{wristleft_pwm}_{claw_pwm}_{gantry_pwm}_{shoulder_pwm}"

def send_packet(packet):
    """Send a packet to the rover."""
    rover_socket.sendto(packet.encode('utf-8'), (ROVER_IP, ROVER_PORT))
    print(f"Sent packet: {packet}")

def get_pwm_drive_input(keys, forward_speed=148, reverse_speed=108):
    """Get PWM values for driving based on keyboard input."""
    left_wheel_pwm = [128, 128, 128]
    right_wheel_pwm = [128, 128, 128]

    if keys[pygame.K_w]:
        left_wheel_pwm = [forward_speed, forward_speed, forward_speed]
        right_wheel_pwm = [forward_speed, forward_speed, forward_speed]
    elif keys[pygame.K_s]:
        left_wheel_pwm = [reverse_speed, reverse_speed, reverse_speed]
        right_wheel_pwm = [reverse_speed, reverse_speed, reverse_speed]

    if keys[pygame.K_a]:  # Turn left
        left_wheel_pwm = [reverse_speed, reverse_speed, reverse_speed]
        right_wheel_pwm = [forward_speed, forward_speed, forward_speed]
    elif keys[pygame.K_d]:  # Turn right
        left_wheel_pwm = [forward_speed, forward_speed, forward_speed]
        right_wheel_pwm = [reverse_speed, reverse_speed, reverse_speed]

    return left_wheel_pwm, right_wheel_pwm

def get_pwm_arm_input(keys):
    """Get PWM values for the arm based on keyboard input."""
    shoulder_pwm = 128
    wristright_pwm = 128
    wristleft_pwm = 128
    claw_pwm = 128
    gantry_pwm = 128
    elbow_pwm = 128

    if keys[pygame.K_q]:  # Open claw
        claw_pwm = 148
    elif keys[pygame.K_e]:  # Close claw
        claw_pwm = 108

    if keys[pygame.K_x]:  # Move elbow up
        elbow_pwm = 148
    elif keys[pygame.K_z]:  # Move elbow down
        elbow_pwm = 108

    if keys[pygame.K_UP]:  # Gantry up
        wristright_pwm = 148
        wristleft_pwm = 108
    elif keys[pygame.K_DOWN]:  # Gantry down
        wristright_pwm = 108
        wristleft_pwm = 148

    if keys[pygame.K_LEFT]:  # Wrist rotate left
        wristright_pwm = 108
        wristleft_pwm = 108
    elif keys[pygame.K_RIGHT]:  # Wrist rotate right
        wristright_pwm = 148
        wristleft_pwm = 148

    if keys[pygame.K_r]:  # Shoulder clockwise
        shoulder_pwm = 148
    elif keys[pygame.K_f]:  # Shoulder counterclockwise
        shoulder_pwm = 108

    return shoulder_pwm, wristright_pwm, wristleft_pwm, claw_pwm, gantry_pwm, elbow_pwm

async def handle_connection(websocket, path):
    """WebSocket connection handler."""
    global prev_left_wheel_pwm, prev_right_wheel_pwm, prev_arm_pwm

    while True:
        keys = pygame.key.get_pressed()

        # Generate packets for drive and arm
        left_wheel_pwm, right_wheel_pwm = get_pwm_drive_input(keys)
        arm_pwms = get_pwm_arm_input(keys)

        # Check if drive or arm PWMs have changed
        if (left_wheel_pwm != prev_left_wheel_pwm) or (right_wheel_pwm != prev_right_wheel_pwm):
            drive_packet = create_drive_packet(right_wheel_pwm, left_wheel_pwm)
            await websocket.send(drive_packet)
            send_packet(drive_packet)
            prev_left_wheel_pwm, prev_right_wheel_pwm = left_wheel_pwm, right_wheel_pwm

        if arm_pwms != prev_arm_pwm:
            arm_packet = create_arm_packet(*arm_pwms)
            await websocket.send(arm_packet)
            send_packet(arm_packet)
            prev_arm_pwm = arm_pwms

        await asyncio.sleep(0.1)  # Adjust as needed

async def main():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Rover Control")

    # Start WebSocket server
    start_server = websockets.serve(handle_connection, "0.0.0.0", 8080)

    async with start_server:
        while True:
            # Handle Pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            # Fill the screen with a color (optional, just to see it's working)
            screen.fill((0, 0, 0))
            pygame.display.flip()

            await asyncio.sleep(0.01)  # Adjust as needed to avoid high CPU usage

if __name__ == "__main__":
    asyncio.run(main())
