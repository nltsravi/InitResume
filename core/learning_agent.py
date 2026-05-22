import os
import json
from sqlalchemy.orm import Session
from database import Job, Application
from scoring import load_weights, save_weights

class LearningAgent:
    @staticmethod
    def process_rejection(db: Session, company_name: str, job_title: str) -> dict:
        """
        Processes a rejection email event by looking up the historical match score
        and adjusting the matching engine weights dynamically.
        """
        print(f"[LearningAgent] Processing rejection for company='{company_name}', role='{job_title}'...")
        
        # Look up application history in DB
        app_record = db.query(Application).join(Job).filter(
            Job.company.ilike(company_name.strip()),
            Job.title.ilike(job_title.strip())
        ).first()
        
        if not app_record:
            return {"status": "ignored", "reason": "No matching application found in database"}
            
        # Update the application status to 'Rejected'
        app_record.status = "Rejected"
        db.commit()
        
        # Adjust matching engine weights based on the rejection feedback
        weights = load_weights()
        
        # Dynamic feedback loop adjustment rule:
        # If we got rejected on a role where tech score was weighted highly but we failed,
        # we might slightly reduce the tech similarity weight and distribute it to domain/role relevance
        # to focus on better role/domain alignment.
        if weights["w_tech"] > 0.25:
            weights["w_tech"] -= 0.02
            weights["w_domain"] += 0.01
            weights["w_role"] += 0.01
            
            # Normalize to ensure weights sum to exactly 1.0
            total = sum(weights.values())
            for key in weights:
                weights[key] = round(weights[key] / total, 2)
                
            save_weights(weights)
            print(f"[LearningAgent] Adjusted matching weights: {weights}")
            return {
                "status": "weights_adjusted", 
                "new_weights": weights,
                "score_at_rejection": app_record.match_score
            }
            
        return {"status": "no_change", "reason": "Weights already optimized to safety floor"}
