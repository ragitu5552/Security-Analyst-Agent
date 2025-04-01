import sqlite3
from groq import Groq
import re
import os
from dotenv import load_dotenv

load_dotenv()

class SecurityQuerySystem:
    def __init__(self, db_path="security.db"):
        self.db_path = db_path
        self.client = self._initialize_groq_client()
        
    def _initialize_groq_client(self):
        """Initialize Groq client with API key from environment variables"""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")
        return Groq(api_key=api_key)
        
    def query_database(self, user_query):
        """Query the database based on user input and return relevant results"""
        conn = None
        try:
            conn = sqlite3.connect("security.db")
            cursor = conn.cursor()
            
            entities = self._extract_entities(user_query)
            sql_query, params = self._build_sql_query(user_query, entities)
            cursor.execute(sql_query, params)
            results = cursor.fetchall()

            formatted_results = self._format_results(results)
            
            return formatted_results
            
        except sqlite3.Error as e:
            return f"Database error: {str(e)}"
        finally:
            if conn:
                conn.close()
    
    def _extract_entities(self, text):
        """Extract relevant entities from user query"""
        entities = {
            'objects': [],
            'times': [],
            'locations': []
        }
 
        object_pattern = re.compile(r'\b(?:truck|car|person|vehicle|Ford F150|sedan|SUV|bike|motorcycle|pedestrian)\b', re.IGNORECASE)
        time_pattern = re.compile(r'\b(?:[0-9]{1,2}:[0-9]{2}(?::[0-9]{2})?(?:\s?[APap][mM])?|midnight|noon|morning|afternoon|evening|night)\b', re.IGNORECASE)
        location_pattern = re.compile(r'\b(?:gate|garage|main entrance|north side|south side|east side|west side|parking lot|backyard|front yard)\b', re.IGNORECASE)
        
        entities['objects'] = list(set(object_pattern.findall(text)))  # Remove duplicates
        entities['times'] = list(set(time_pattern.findall(text)))
        entities['locations'] = list(set(location_pattern.findall(text)))
        
        return entities
    
    def _build_sql_query(self, user_query, entities):
        """Build SQL query with parameters to prevent SQL injection"""
        base_query = "SELECT timestamp, object_type, object_details, location FROM events WHERE "
        conditions = []
        params = []
        
        if entities['objects']:
            obj_conditions = " OR ".join(["object_type LIKE ?"] * len(entities['objects']))
            conditions.append(f"({obj_conditions})")
            params.extend([f"%{obj}%" for obj in entities['objects']])
            
        if entities['times']:
            time_conditions = " OR ".join(["timestamp LIKE ?"] * len(entities['times']))
            conditions.append(f"({time_conditions})")
            params.extend([f"%{time}%" for time in entities['times']])
            
        if entities['locations']:
            loc_conditions = " OR ".join(["location LIKE ?"] * len(entities['locations']))
            conditions.append(f"({loc_conditions})")
            params.extend([f"%{loc}%" for loc in entities['locations']])
            
        if not conditions:
            return "SELECT timestamp, object_type, object_details, location FROM events ORDER BY timestamp DESC LIMIT 10", []
            
        return base_query + " AND ".join(conditions) + " ORDER BY timestamp DESC", params
    
    def _format_results(self, results):
        """Format database results for LLM processing"""
        if not results:
            return "No matching events found in the database."
            
        formatted = "Database query results:\n"
        for idx, (timestamp, obj_type, details, location) in enumerate(results, 1):
            formatted += f"{idx}. {timestamp} - {obj_type} ({details}) at {location}\n"
            
        return formatted
    
    def generate_response(self, user_query):
        """Generate a natural language response using Groq API"""
        try:
            db_results = self.query_database(user_query)

            prompt = f"""
            You are a security analyst assistant for a drone surveillance system. 
            A user has asked: "{user_query}"
            
            Here are relevant security events from our database:
            {db_results}
            
            Please provide a concise, helpful response to the user's query based on this information.
            If no relevant events were found, politely inform the user.
            Include specific details from the database when available.
            """
            
            # Call Groq API
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful security analyst assistant for a drone surveillance system. Provide accurate information based on the database results."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama3-70b-8192",
                temperature=0.3,
                max_tokens=1024
            )
            
            return chat_completion.choices[0].message.content
            
        except Exception as e:
            return f"Error generating response: {str(e)}"

def main():
    try:
        query_system = SecurityQuerySystem()
        
        print("Drone Security Analyst Query System")
        print("Type 'quit' to exit\n")
        
        while True:
            user_input = input("\nEnter your security query: ").strip()
            if user_input.lower() == 'quit':
                break
                
            if not user_input:
                print("Please enter a valid query.")
                continue
                
            print("\nProcessing your query...")
            response = query_system.generate_response(user_input)
            print("\nResponse:")
            print(response)
            
    except Exception as e:
        print(f"System error: {str(e)}")

if __name__ == "__main__":
    main()