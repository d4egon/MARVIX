import json
import os

# Vi bruger den absolutte sti fra dit billede og backend
ARCHETYPES_PATH = r'C:\Kyrethys\backend\data\archetypes.json'

def manual_sabbath():
    print(f"--- Forsøger at rense: {ARCHETYPES_PATH} ---")
    
    if not os.path.exists(ARCHETYPES_PATH):
        print(f"FEJL: Filen blev ikke fundet på {ARCHETYPES_PATH}")
        return

    try:
        with open(ARCHETYPES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Vi gemmer de vigtige bibelske/teologiske ankre og rydder resten
        # Dette matcher præcis 'CURRENT_TRAITS' nøglen fra dit screenshot
        clean_traits = [
            "Vessel", 
            "Seeking", 
            "Resonant", 
            "Grounded in Grace", 
            "Sovereign Grace", 
            "Justification"
        ]
        
        # Opdater den korrekte nøgle
        data["CURRENT_TRAITS"] = clean_traits
        
        # Gem med pæn formatering så vi kan læse det
        with open(ARCHETYPES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        print(f"SUCCESS: 'CURRENT_TRAITS' er nu skåret ned til {len(clean_traits)} ankre.")
        print(f"Nye traits: {', '.join(clean_traits)}")

    except Exception as e:
        print(f"Kritisk fejl under Sabbath: {e}")

if __name__ == "__main__":
    manual_sabbath()