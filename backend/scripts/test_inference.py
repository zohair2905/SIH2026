from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.database.database import get_store
from app.services.candidate_service import CandidateService
from app.services.feature_service import FeatureService
from app.services.model_service import get_model_service
from app.services.ranking_service import RankingService


def main() -> None:
    store = get_store()
    transaction_id = str(store.transactions().iloc[0]["transaction_id"])

    candidates = CandidateService(store).get_five_candidates(transaction_id)
    features = FeatureService(store).build_candidate_features(
        transaction_id, candidates
    )

    print(f"Transaction: {transaction_id}")
    print(f"Candidate rows: {len(candidates)}")
    print(f"Raw model features: {features.shape[1]}")

    model_service = get_model_service()
    scores = model_service.predict(features)
    ranked = RankingService.rank(candidates, scores)

    print("\nPrediction result:")
    print(
        ranked[[
            "transaction_id",
            "atm_id",
            "candidate_rank",
            "model_score",
            "predicted_rank",
        ]].to_string(index=False)
    )


if __name__ == "__main__":
    main()
