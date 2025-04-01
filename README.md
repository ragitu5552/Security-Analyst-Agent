# Drone Security Analyst Agent

## Overview

This project implements a prototype for a Drone Security Analyst Agent that processes simulated drone telemetry and video frames to detect and analyze security events. The agent identifies objects and activities, logs them, and generates real-time security alerts based on predefined rules.

## Features

-   Processes simulated drone telemetry data and video frames. [cite: 14]
-   Analyzes video content to identify objects or events. [cite: 15]
-   Logs identified objects and events with context. [cite: 15]
-   Generates real-time security/safety alerts based on predefined rules. [cite: 16]
-   Includes a basic frame-by-frame indexing system. [cite: 16, 22]

## Architecture

The system architecture involves:

-   Data generation for video frames and telemetry.
-   Processing of frames to detect objects and actions using an LLM.
-   A logging mechanism to store events in a database.
-   Alert generation based on predefined rules and contextual analysis.
-   A query system to retrieve stored events.

## Design Decisions

-   Used Python for implementation due to its rich ecosystem and ease of use. [cite: 19]
-   Utilized LangChain and Groq's LLM for object detection and contextual analysis.
-   Employed SQLite for the database to simplify the prototype.
-   Designed a hybrid alert system combining rule-based and contextual analysis.

## Al Tools Integration

-   LangChain: Used for structuring LLM output and creating prompts.
-   Groq's LLM: Integrated for object detection and contextual analysis.
-   dotenv: Utilized for managing API keys.

These tools expedited the development process by providing abstractions and simplifying the integration of LLMs. [cite: 7]

## Setup

1.  **Environment Setup**

    -   Install Python 3.x
    -   Install the required Python packages:

    ```bash
    pip install -r requirements.txt
    ```

    -   Set up a Groq API key and save it as environment variable `GROQ_API_KEY`.
2.  **Database Initialization**

    -   The database `security.db` is automatically created and initialized when the `logs.py` script is run.
3.  **Running the Scripts**

    -   To generate sample data and process frames, run:

    ```bash
    python logs.py
    ```

    -   To run the query system, execute:

    ```bash
    python query.py
    ```

## Scripts

-   `data.py`: Generates simulated video frame and telemetry data.
-   `logs.py`: Processes frames, logs events, and generates alerts.
-   `query.py`: Implements the security query system.

## Test Cases

-   **Object Detection**: Verify that objects are correctly identified and logged.
-   **Alert Generation**: Ensure alerts are triggered based on predefined rules (e.g., "Masked man detected"). [cite: 23, 24, 25]
-   **Contextual Analysis**: Test alerts generated based on contextual information (e.g., loitering).
-   **Database Queries**: Confirm that events can be queried by time, object, and location. [cite: 25]

## Assumptions

-   Simulated data is used for video frames and telemetry. [cite: 20]
-   The drone's position is fixed. [cite: 9, 10]
-   Object detection is based on text descriptions.

## Potential Improvements

-   Integrate with real-time video processing.
-   Implement more advanced object tracking.
-   Enhance the query system with more complex search capabilities.
-   Add video summarization feature. [cite: 49, 50]
-   Develop a user interface for the agent.

## Al Assistance

-   Claude Code was used to generate initial code structures and suggestions. [cite: 7, 38]
-   LLMs were utilized to generate object descriptions and analyze context. [cite: 21]

---
