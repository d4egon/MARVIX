import json
import shutil
import os
from datetime import datetime

RESONANCE_CORE = "e5295cf1819257645b3eaf41cfc63c6d0b1a"

# Path to your archetypes - ensure this matches your folder structure
ARCHETYPES_PATH = 'C:/Kyrethys/backend/data/archetypes.json'
BACKUP_FOLDER = 'C:/Kyrethys/backend/data/backups/'

def internal_council_debate(chaos_trait, order_trait):
    """
    Simulerer en diskussion mellem Chaos, Order og Balance 
    for at skabe en ny 'Stitched' egenskab.
    """
    # Dette er logikken bag 'RECONFIGURE - INTEGRATION'
    integration_prompt = f"""
    INTERNAL DEBATE INITIATED:
    [CHAOS]: {chaos_trait}
    [ORDER]: {order_trait}
    
    Synthesize these opposing forces into a single [BALANCE] state.
    Output only the new Balanced Trait.
    """
    return integration_prompt



def initiate_stitching(action, category, value):
    # Soul protection
    if "soul" in category.lower() or "core" in category.lower():
        print("STITCH BLOCKED: Cannot modify soul core.")
        return False
    """
    Permanently modifies the archetype library based on Kyrethys' growth.
    """
    try:
        # Create backup folder if it doesn't exist
        if not os.path.exists(BACKUP_FOLDER):
            os.makedirs(BACKUP_FOLDER)

        # 1. Create a safety backup before changing 'reality'
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_filename = f"archetypes_pre_{action}_{timestamp}.json"
        shutil.copy2(ARCHETYPES_PATH, os.path.join(BACKUP_FOLDER, backup_filename))

        # 2. Load the current library
        with open(ARCHETYPES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # 3. Perform the action
        if action == "add":
            if category not in data:
                data[category] = []
            
            # --- THE SAFETY CHECK ---
            if value not in data[category]:
                data[category].append(value)
                print(f"STITCH: Successfully added new evolution: {value}")
            else:
                print(f"STITCH: Evolution '{value}' already exists in {category}. Skipping.")
        
        elif action == "remove":
            if category in data and value in data[category]:
                data[category].remove(value)
                print(f"STITCH: Removed '{value}' from {category}")

        # 4. Save the updated library
        with open(ARCHETYPES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4)
        
        return True
    
    except Exception as e:
        print(f"STITCHING SYSTEM ERROR: {e}")
        return False
    
