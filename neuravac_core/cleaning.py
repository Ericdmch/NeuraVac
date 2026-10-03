from dataclasses import asdict, dataclass

from neuravac_core.config import CleaningConfig


@dataclass
class CleaningAttempt:
    region_id: str
    before_score: float
    after_score: float
    improvement: float
    pass_number: int
    success: bool
    duration_s: float

    def to_dict(self) -> dict:
        return asdict(self)


def evaluate_pass(
    region_id: str,
    before: float,
    after: float,
    pass_number: int,
    duration: float,
    config: CleaningConfig,
) -> CleaningAttempt:
    if before < 0 or after < 0:
        raise ValueError("debris observations must be nonnegative")
    return CleaningAttempt(
        region_id,
        before,
        after,
        before - after,
        pass_number,
        after <= config.success_threshold,
        duration,
    )


def should_retry(attempt: CleaningAttempt, config: CleaningConfig) -> bool:
    return (
        not attempt.success
        and attempt.pass_number <= config.max_retries
        and attempt.improvement >= config.minimum_improvement
    )
