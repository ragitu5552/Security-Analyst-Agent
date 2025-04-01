import os
import datetime
import json
import data
import sqlite3
from collections import defaultdict
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain.chat_models import init_chat_model

load_dotenv()

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
            frame_description TEXT,
            action TEXT,
            location TEXT,
            context TEXT
        )
        ''')
        self.conn.commit()

    def log_detection(self, obj: DetectedObject, frame_desc: str):
        obj_id = _generate_object_identifier(obj)
        now = datetime.datetime.now()

        recent = [t for t in self.memory.get(obj_id, []) if now - t < datetime.timedelta(minutes=10)]

        context = f"(seen {len(recent) + 1} times since {recent[0].strftime('%H:%M')})" if recent else "(first detection)"
        cursor = self.conn.cursor()
        cursor.execute('''
        INSERT INTO events (object_type, object_details, frame_description, action, location, context)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            obj.object_type,
            json.dumps(obj.object_details),
            frame_desc,
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
api_key=os.environ["GROQ_API_KEY"]
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
        "action": None,  
        "location": None,  
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
        "frequency_window": 60  #minutes
    }
]


class ContextualAlertAnalyzer:
    def __init__(self, db_conn: sqlite3.Connection):
        self.conn = db_conn  
        self.llm = init_chat_model("llama-3.3-70b-versatile", model_provider="groq")
        self.alert_prompt = ChatPromptTemplate.from_messages([
            ("system", """Analyze this security event in context of recent activity. Consider:
            - Is this behavior normal for this location/time?
            - Does it match any suspicious patterns?
            - Is there escalation of concerning activity?
            
            Recent events in this location (last 2 hours):
            {recent_events}
            
            Current event:
            {current_event}
            
            Return either:
            - "OK" if nothing concerning
            - OR a brief alert message explaining the concern"""),
            ("human", "Should we alert security about this?")
        ])

    def get_recent_events(self, location: str, timestamp: datetime.datetime) -> str:
        """Get recent events from the same location"""
        cutoff = timestamp - datetime.timedelta(hours=2)
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT object_type, action, context 
            FROM events 
            WHERE location = ? AND timestamp > ?
            ORDER BY timestamp DESC
            LIMIT 5
        ''', (location, cutoff))
        return "\n".join(
            f"{row[0]} {row[1]} {row[2]}" 
            for row in cursor.fetchall()
        )

    def analyze_context(self, obj: DetectedObject, timestamp: datetime.datetime) -> Optional[str]:
        """Use LLM to analyze context and return alert message if needed"""
        recent_events = self.get_recent_events(obj.location, timestamp)
        current_event_str = f"{obj.object_type} {obj.action} at {obj.location}"
        
        response = self.llm.invoke(self.alert_prompt.invoke({
            "recent_events": recent_events,
            "current_event": current_event_str
        }))
        
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        if response_text.strip().upper() == "OK" or response_text.startswith("OK"):
            return None
        #return response_text
        return None


class EnhancedSecurityLogger(SecurityLogger):
    def __init__(self):
        super().__init__()
        self.context_analyzer = ContextualAlertAnalyzer(self.conn)
        
    def check_alerts(self, obj: DetectedObject, timestamp: datetime.datetime) -> List[str]:
        """Hybrid alert detection combining rules and contextual analysis"""
        alerts = []
        
        # 1. Checking predefined rules
        for rule in alert_rules:
            if self._matches_rule(obj, rule):
                if self._passes_frequency_check(obj, rule, timestamp):
                    alerts.append(rule["alert_message"])
        
        # 2. Contextual analysis 
        if not alerts:  
            contextual_alert = self.context_analyzer.analyze_context(obj, timestamp)
            if contextual_alert:
                alerts.append(f"CONTEXT ALERT: {contextual_alert}")
        
        return alerts
    
    def _matches_rule(self, obj: DetectedObject, rule: Dict) -> bool:
        """Check if object matches rule criteria"""
        return ((rule["object"] is None or rule["object"] == obj.object_type) and
                (rule["action"] is None or rule["action"] == obj.action) and
                (rule["location"] is None or rule["location"] == obj.location))
    
    def _passes_frequency_check(self, obj: DetectedObject, rule: Dict, timestamp: datetime.datetime) -> bool:
        """Check frequency thresholds if they exist"""
        if "frequency_threshold" not in rule:
            return True
            
        obj_id = _generate_object_identifier(obj)
        window = datetime.timedelta(minutes=rule["frequency_window"])
        recent = [t for t in self.memory.get(obj_id, []) if timestamp - t < window]
        return len(recent) >= rule["frequency_threshold"]


logger = EnhancedSecurityLogger()

def process_frame(frame_description: str, frame_timestamp_str: str):
    """Enhanced frame processing with hybrid alerts"""
    detected_obj = structured_llm.invoke(prompt_template.invoke({"text": frame_description}))
    frame_timestamp = datetime.datetime.strptime(frame_timestamp_str, "%Y-%m-%d %H:%M:%S")
    
    logger.log_detection(detected_obj, frame_description)
    alerts = logger.check_alerts(detected_obj, frame_timestamp)
    
    if alerts:
        for alert in alerts:
            print(f"🚨 {alert}")
    else:
        print(f"👍 Okay")


# Process sample frames
frames, _ = data.generate_surveillance_data(5)  
for frame in frames:
    if frame["object"] != "Empty":
        process_frame(frame["description"], frame["timestamp"])