# import os
# import datetime
# import json
# import data
# import sqlite3
# from collections import defaultdict
# from typing import Optional
# from pydantic import BaseModel, Field
# from langchain_core.prompts import ChatPromptTemplate
# from langchain.chat_models import init_chat_model

# class DetectedObject(BaseModel):
#     object_type: str = Field(..., description="Category: person/vehicle/animal")
#     object_details: dict = Field(default_factory=dict, description="Attributes like color, model, clothing")
#     action: str = Field(..., description="What the object is doing")
#     location: str = Field(..., description="Where detected")

# def _generate_object_identifier(obj: DetectedObject) -> str:
#     details = obj.object_details
#     if obj.object_type == "vehicle":
#         return f"{details.get('color','unknown')}_{obj.object_type}_{details.get('model','')}"
#     elif obj.object_type == "person":
#         return f"{details.get('clothing','unknown')}_{obj.object_type}"
#     else:
#         return f"{obj.object_type}_{obj.location}"

# class SecurityLogger:
#     def __init__(self):
#         self.conn = sqlite3.connect('security.db')
#         self._init_db()
#         self.memory = defaultdict(list)
        
#     def _init_db(self):
#         cursor = self.conn.cursor()
#         cursor.execute('''
#             CREATE TABLE IF NOT EXISTS events (
#                 id INTEGER PRIMARY KEY,
#                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
#                 object_type TEXT,
#                 object_details JSON,
#                 action TEXT,
#                 location TEXT,
#                 context TEXT
#             )
#         ''')
#         self.conn.commit()

#     def log_detection(self, obj: DetectedObject):
#         obj_id = _generate_object_identifier(obj)
#         now = datetime.datetime.now()
        
#         # Check recent occurrences
#         recent = [t for t in self.memory.get(obj_id, []) 
#                  if now - t < datetime.timedelta(minutes=30)]
        
#         # Build context
#         context = ""
#         if recent:
#             context = f"(seen {len(recent)+1} times since {recent[0].strftime('%H:%M')})"
#         else:
#             context = "(first detection)"
        
#         # Store in SQLite
#         cursor = self.conn.cursor()
#         cursor.execute('''
#             INSERT INTO events 
#             (object_type, object_details, action, location, context)
#             VALUES (?, ?, ?, ?, ?)
#         ''', (
#             obj.object_type,
#             json.dumps(obj.object_details),
#             obj.action,
#             obj.location,
#             context
#         ))
#         self.conn.commit()
        
#         # Update memory
#         self.memory[obj_id].append(now)
        
#         # Clean old entries
#         self._clean_memory()

#     def _clean_memory(self):
#         cutoff = datetime.datetime.now() - datetime.timedelta(minutes=30)
#         for obj_id in list(self.memory.keys()):
#             self.memory[obj_id] = [t for t in self.memory[obj_id] if t > cutoff]
#             if not self.memory[obj_id]:
#                 del self.memory[obj_id]

# # Initialize components
# logger = SecurityLogger()
# os.environ["GROQ_API_KEY"] = "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"
# llm = init_chat_model("llama-3.3-70b-versatile", model_provider="groq")
# structured_llm = llm.with_structured_output(schema=DetectedObject)

# prompt_template = ChatPromptTemplate.from_messages([
#     ("system", """Extract security-related objects and activities. Return:
#      - object_type (person/vehicle/animal)
#      - object_details (color, model, clothing if available)
#      - action
#      - location"""),
#     ("human", "{text}")
# ])

# def process_frame(frame_description: str):
#     # Extract entities directly into DetectedObject format
#     detected_obj = structured_llm.invoke(prompt_template.invoke({"text": frame_description}))
    
    
#     logger.log_detection(detected_obj)

# # Process generated frames
# frames, _ = data.generate_surveillance_data(1)
# for frame in frames:
#     if frame["object"] != "Empty":
#         print(process_frame(frame["description"]))


import os
import datetime
import json
import data
import sqlite3
from collections import defaultdict
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model


class DetectedObject(BaseModel):
    object_type: str = Field(..., description="Category: person/vehicle/animal")
    object_details: dict = Field(default_factory=dict, description="Attributes like color, model, clothing")
    action: str = Field(..., description="What the object is doing")
    location: str = Field(..., description="Where detected")


def _generate_object_identifier(obj: DetectedObject) -> str:
    details = obj.object_details
    if obj.object_type == "vehicle":
        return f"{details.get('color','unknown')}_{obj.object_type}_{details.get('model','')}"
    elif obj.object_type == "person":
        return f"{details.get('clothing','unknown')}_{obj.object_type}"
    else:
        return f"{obj.object_type}_{obj.location}"


class SecurityLogger:
    def __init__(self):
        self.conn = sqlite3.connect('security.db')
        self._init_db()
        self.memory: Dict[str, List[datetime.datetime]] = defaultdict(list)  

    def _init_db(self):
        cursor = self.conn.cursor()
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            object_type TEXT,
            object_details JSON,
            action TEXT,
            location TEXT,
            context TEXT
        )
        ''')
        self.conn.commit()

    def log_detection(self, obj: DetectedObject):
        obj_id = _generate_object_identifier(obj)
        now = datetime.datetime.now()

        recent = [t for t in self.memory.get(obj_id, []) if now - t < datetime.timedelta(minutes=30)]

        context = f"(seen {len(recent) + 1} times since {recent[0].strftime('%H:%M')})" if recent else "(first detection)"
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO events (object_type, object_details, action, location, context)
        VALUES (?, ?, ?, ?, ?)
        ''', (
            obj.object_type,
            json.dumps(obj.object_details),
            obj.action,
            obj.location,
            context
        ))
        self.conn.commit()
        self.memory[obj_id].append(now)
        self._clean_memory()

    def _clean_memory(self):
        cutoff = datetime.datetime.now() - datetime.timedelta(minutes=30)
        for obj_id in list(self.memory.keys()):
            self.memory[obj_id] = [t for t in self.memory[obj_id] if t > cutoff]
            if not self.memory[obj_id]:
                del self.memory[obj_id]



logger = SecurityLogger()
os.environ["GROQ_API_KEY"] = "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"
llm = init_chat_model("llama-3.3-70b-versatile", model_provider="groq")
structured_llm = llm.with_structured_output(schema=DetectedObject)

prompt_template = ChatPromptTemplate.from_messages([
    ("system", """Extract security-related objects and activities. Return:
    - object_type (person/vehicle/animal)
    - object_details (color, model, clothing if available)
    - action
    - location"""),
    ("human", "{text}")
])

# --- Alert Rules ---
alert_rules = [
    {
        "object": "Masked man",
        "action": None,  # Any action
        "location": None,  # Any location
        "alert_message": "Masked man detected!"
    },
    {
        "object": None,
        "action": "tampering with lock",
        "location": None,
        "alert_message": "Tampering with lock detected!"
    },
    {
        "object": "Masked man",
        "action": None,
        "location": "Fence",
        "alert_message": "Masked man detected at the fence!"
    },
    {
        "object": "Random person",
        "action": "loitering",
        "location": "Main gate",
        "alert_message": "Random person loitering at main gate!",
        "frequency_threshold": 3,
        "frequency_window": 60  # minutes
    }
]


def check_alerts(obj: DetectedObject, timestamp: datetime.datetime) -> List[str]:
    """
    Checks if a detected object triggers any alert rules.
    Considers object, action, location, and frequency.

    Args:
        obj: The DetectedObject.
        timestamp: The timestamp of the detection.

    Returns:
        A list of alert messages.
    """
    triggered_alerts = []
    for rule in alert_rules:
        if (rule["object"] is None or rule["object"] == obj.object_type) and \
           (rule["action"] is None or rule["action"] == obj.action) and \
           (rule["location"] is None or rule["location"] == obj.location):

            # Frequency check
            if "frequency_threshold" in rule and "frequency_window" in rule:
                obj_id = _generate_object_identifier(obj)
                recent_occurrences = [
                    t for t in logger.memory.get(obj_id, [])
                    if timestamp - t < datetime.timedelta(minutes=rule["frequency_window"])
                ]
                if len(recent_occurrences) >= rule["frequency_threshold"]:
                    triggered_alerts.append(rule["alert_message"])
            else:
                triggered_alerts.append(rule["alert_message"])

    return triggered_alerts


def process_frame(frame_description: str, frame_timestamp_str: str):
    """
    Processes a frame description, extracts object information, logs it, and checks for alerts.
    """
    detected_obj = structured_llm.invoke(prompt_template.invoke({"text": frame_description}))
    frame_timestamp = datetime.datetime.strptime(frame_timestamp_str, "%Y-%m-%d %H:%M:%S")

    logger.log_detection(detected_obj)
    alerts = check_alerts(detected_obj, frame_timestamp)
    for alert in alerts:
        print(f"ALERT: {alert}")


frames, _ = data.generate_surveillance_data(50)  
for frame in frames:
    if frame["object"] != "Empty":
        process_frame(frame["description"], frame["timestamp"])

