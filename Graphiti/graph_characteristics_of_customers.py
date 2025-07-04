import asyncio
import json
import logging
import os
from datetime import datetime, timedelta, timezone

from graphiti_core import Graphiti
from graphiti_core.nodes import EpisodeType

# ============================
# Real-World Use Case: Personal Fitness Tracker
# ============================
# Scenario:
#   A fitness app tracks user activities (running, cycling, workouts) over time.
#   Each activity is represented as structured JSON and ingested as an "episode".
#   Later, the app can query:
#     1) "What activities did I perform in the last week?"
#     2) "Which running activities were > 5 km?"
#     3) "Show me all activities in the last month."
#
# This script:
#   1. Connects to Neo4j via Graphiti
#   2. Builds indices & constraints (one-time)
#   3. Creates three JSON‐encoded episodes (A1, A2, A3)
#   4. Adds them to Graphiti
#   5. Runs three searches and prints out the results

# ----------------------------
# Configure Logging & Neo4j
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

NEO4J_URI      = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER     = os.environ.get("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD", None)

if not NEO4J_URI or not NEO4J_USER or not NEO4J_PASSWORD:
    raise ValueError("❗️ You must set NEO4J_URI, NEO4J_USER, and NEO4J_PASSWORD")

# ----------------------------
# Helpers: ISO timestamp N days ago
# ----------------------------
def iso_timestamp_days_ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

# ----------------------------
# Create sample episodes as JSON
# ----------------------------
def create_sample_episodes():
    episodes = []

    # Activity A1: John ran 6 km, 7 days ago
    content_a1 = {
        "user": "john_doe",
        "activity_id": "activity_a1",
        "activity_type": "running",
        "distance_km": 6,
        "duration_min": 35,
        "timestamp": iso_timestamp_days_ago(7),
    }
    episodes.append({
        "name": "Fitness Event A1",
        "body": json.dumps(content_a1),
        "type": EpisodeType.json,
        "description": "7 days ago: John ran 6 km",
    })

    # Activity A2: John cycled 20 km, 3 days ago
    content_a2 = {
        "user": "john_doe",
        "activity_id": "activity_a2",
        "activity_type": "cycling",
        "distance_km": 20,
        "duration_min": 60,
        "timestamp": iso_timestamp_days_ago(3),
    }
    episodes.append({
        "name": "Fitness Event A2",
        "body": json.dumps(content_a2),
        "type": EpisodeType.json,
        "description": "3 days ago: John cycled 20 km",
    })

    # Activity A3: John ran 4 km, 2 days ago
    content_a3 = {
        "user": "john_doe",
        "activity_id": "activity_a3",
        "activity_type": "running",
        "distance_km": 4,
        "duration_min": 25,
        "timestamp": iso_timestamp_days_ago(2),
    }
    episodes.append({
        "name": "Fitness Event A3",
        "body": json.dumps(content_a3),
        "type": EpisodeType.json,
        "description": "2 days ago: John ran 4 km",
    })

    return episodes

# ----------------------------
# Query Functions (Hybrid/Natural-Language)
# ----------------------------
async def query_recent_activities(graphiti: Graphiti, user: str, days: int):
    since_time = iso_timestamp_days_ago(days)
    query_text = f"{user} activity since {since_time}"
    logger.info(f"🔍 Querying recent activities: \"{query_text}\"")
    results = await graphiti.search(query=query_text)
    return results

async def query_running_over_distance(graphiti: Graphiti, user: str, min_distance: float, days: int):
    since_time = iso_timestamp_days_ago(days)
    query_text = f"{user} running distance > {min_distance} since {since_time}"
    logger.info(f"🔍 Querying running > {min_distance} km: \"{query_text}\"")
    results = await graphiti.search(query=query_text)
    return results

async def query_monthly_progress(graphiti: Graphiti, user: str):
    since_time = iso_timestamp_days_ago(30)
    query_text = f"{user} activity since {since_time}"
    logger.info(f"🔍 Querying monthly progress: \"{query_text}\"")
    results = await graphiti.search(query=query_text)
    return results

# ----------------------------
# Main Async Routine
# ----------------------------
async def main():
    # 1) Initialize Graphiti client (connect to Neo4j)
    graphiti = Graphiti(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

    try:
        # 2) Build indices & constraints (run once per fresh database)
        await graphiti.build_indices_and_constraints()
        logger.info("✔ Indices and constraints built.")

        # 3) Create & add sample episodes
        sample_episodes = create_sample_episodes()
        for ep in sample_episodes:
            await graphiti.add_episode(
                name=ep["name"],
                episode_body=ep["body"],
                source=ep["type"],
                source_description=ep["description"],
                reference_time=datetime.now(timezone.utc),
            )
            logger.info(f"✔ Added episode: {ep['name']}")

        # 4) Query: Activities in the last 5 days
        recent_results = await query_recent_activities(graphiti, "john_doe", days=5)
        print("\n--- Activities in the last 5 days ---")
        for r in recent_results:
            print(f"• UUID: {r.uuid} | Fact: {r.fact} | Time: {r.valid_at or r.ingested_at}")

        # 5) Query: Running activities > 5 km in the last 7 days
        running_results = await query_running_over_distance(graphiti, "john_doe", min_distance=5, days=7)
        print("\n--- Running > 5 km in the last 7 days ---")
        for r in running_results:
            print(f"• UUID: {r.uuid} | Fact: {r.fact} | Time: {r.valid_at or r.ingested_at}")

        # 6) Query: All activities in the last 30 days
        monthly_results = await query_monthly_progress(graphiti, "john_doe")
        print("\n--- Activities in the last 30 days ---")
        for r in monthly_results:
            print(f"• UUID: {r.uuid} | Fact: {r.fact} | Time: {r.valid_at or r.ingested_at}")

    finally:
        await graphiti.close()
        logger.info("✔ Graphiti connection closed.")

# ----------------------------
# Entry Point
# ----------------------------
if __name__ == "__main__":
    asyncio.run(main())
