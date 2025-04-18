import random
import datetime
from typing import Dict, List, Tuple

def generate_surveillance_data(num_frames: int = 20) -> Tuple[List[Dict], List[Dict]]:
    """
    Generates simulated video frames and corresponding telemetry data for a fixed-position drone monitoring a gate.
    
    Args:
        num_frames: Number of frames to generate (default: 20)
        
    Returns:
        Tuple containing:
        - List of video frame dictionaries
        - List of telemetry data dictionaries
    """
    
    objects = {
        "Empty": 0.3,
        "Security guard": 0.2,
        "Random person": 0.1,
        "cat": 0.05,
        "Masked man": 0.1,
        "Delivery person": 0.15,
        "Maintenance worker": 0.1,
        "Car": 0.15,
        "Truck": 0.05,
        "Bicycle": 0.05
    }
    
    actions = [
        "standing", "walking", "entering", "exiting", 
        "parking", "unloading", "waiting", "loitering", "inspecting", "tampering with lock"
    ]

    locations = [
        "Main gate", "Parking", "Fence", "Garage"
    ]
    

    base_time = datetime.datetime.combine(datetime.date.today(), datetime.time(6, 0))  # Start at 6AM
    time_increments = [random.randint(1, 180) for _ in range(num_frames)]  # 1-180 seconds between frames
    timestamps = [base_time + datetime.timedelta(seconds=sum(time_increments[:i+1])) for i in range(num_frames)]
    
    frames = []
    telemetry = []
    
    for i in range(num_frames):
        obj = random.choices(list(objects.keys()), weights=list(objects.values()))[0]
        action = random.choice(actions)
        location = random.choice(locations)
        frame_desc = f"{obj} {action} at {location}" if obj != "Empty" else "No activity"
        
        frame_data = {
            "frame_id": i + 1,
            "timestamp": timestamps[i].strftime('%Y-%m-%d %H:%M:%S'),
            "description": frame_desc,
            "object": obj,
            "action": action
        }
        frames.append(frame_data)
        
        telemetry_data = {
            "timestamp": timestamps[i].strftime('%Y-%m-%d %H:%M:%S'),
            "location": "Main Gate",
            "latitude": 37.7749,  # Fixed position
            "longitude": -122.4194,  # Fixed position
            "altitude_m": random.uniform(4.5, 5.5),  # Small variations around 5m
            "heading_deg": 180,  # Fixed orientation
            "speed_mps": 0.0  # Stationary drone
        }
        telemetry.append(telemetry_data)
    
    return frames, telemetry

