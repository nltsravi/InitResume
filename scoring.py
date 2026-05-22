import json
import os

WEIGHTS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "weights.json")

def load_weights() -> dict:
    if os.path.exists(WEIGHTS_FILE):
        try:
            with open(WEIGHTS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Default weights from the matching algorithm
    return {
        "w_tech": 0.40,
        "w_exp": 0.30,
        "w_domain": 0.20,
        "w_role": 0.10
    }

def save_weights(weights: dict):
    with open(WEIGHTS_FILE, "w") as f:
        json.dump(weights, f, indent=4)

def calculate_match_with_weights(s_tech: float, s_exp: float, s_domain: float, s_role: float) -> float:
    """
    Computes matching score using the formula:
    Total Score = (w_tech * s_tech) + (w_exp * s_exp) + (w_domain * s_domain) + (w_role * s_role)
    
    Where:
    - s_tech: semantic similarity of skills (0-100)
    - s_exp: years of experience alignment (18+ years target) (0-100)
    - s_domain: industry relevance e.g. AI, FinTech (0-100)
    - s_role: role relevance e.g. Principal, Staff, Architect (0-100)
    """
    weights = load_weights()
    
    # Normalize inputs to 0-100 if necessary
    score = (
        (weights["w_tech"] * s_tech) +
        (weights["w_exp"] * s_exp) +
        (weights["w_domain"] * s_domain) +
        (weights["w_role"] * s_role)
    )
    return round(score, 2)

def calculate_match(jd_text: str, candidate_profile: dict) -> float:
    """
    Evaluates JD details against the candidate profile.
    """
    # Exposing dynamic component evaluations
    s_tech = 85.0   # Mock similarity score of tech skills
    s_exp = 90.0    # Mock alignment to 18+ years target
    s_domain = 80.0 # Mock relevance of domains (e.g. AI, FinTech)
    s_role = 75.0   # Mock relevance of role title (e.g. Principal)
    
    score = calculate_match_with_weights(s_tech, s_exp, s_domain, s_role)
    
    passed_threshold = score > 75.0
    return passed_threshold, score
