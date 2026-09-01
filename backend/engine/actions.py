"""
Action Mapper
--------------
Maps a diagnosed root cause to a specific, BOUNDED recovery action.
"Bounded" means every action carries an explicit stopping rule (max
retries, cooldown, or "never auto-retry") so the executor can never
loop indefinitely or act outside a compliant envelope.

This is deliberately a simple, auditable lookup table rather than
another rule engine — the diagnosis is where the reasoning complexity
belongs; the action mapping should be boring and predictable.
"""

ACTION_MAP = {
    "network_timeout": {
        "action": "retry_immediate",
        "description": "Retry via the same payment route immediately.",
        "max_attempts": 2,
        "cooldown_minutes": 0,
        "auto_retry": True,
    },
    "issuer_decline": {
        "action": "retry_after_cooldown",
        "description": "Retry after a cooldown period to avoid repeated soft declines.",
        "max_attempts": 2,
        "cooldown_minutes": 360,  # 6 hours
        "auto_retry": True,
    },
    "insufficient_funds": {
        "action": "delayed_retry",
        "description": "Delay retry to allow funds to become available (e.g. after payday).",
        "max_attempts": 1,
        "cooldown_minutes": 4320,  # 3 days
        "auto_retry": True,
    },
    "expired_instrument": {
        "action": "notify_customer",
        "description": "Notify the customer to update their payment instrument. No auto-retry.",
        "max_attempts": 0,
        "cooldown_minutes": 0,
        "auto_retry": False,
    },
    "acquirer_outage": {
        "action": "retry_alternate_route",
        "description": "Retry via an alternate acquirer/route, then escalate if still failing.",
        "max_attempts": 1,
        "cooldown_minutes": 15,
        "auto_retry": True,
    },
    "fraud_hold": {
        "action": "escalate_manual_review",
        "description": "Escalate to manual review. Never auto-retry a fraud/risk hold.",
        "max_attempts": 0,
        "cooldown_minutes": 0,
        "auto_retry": False,
    },
    "ambiguous": {
        "action": "escalate_manual_review",
        "description": "Cause could not be confidently determined. Escalate to manual review.",
        "max_attempts": 0,
        "cooldown_minutes": 0,
        "auto_retry": False,
    },
}


def get_action_for_cause(cause):
    """Returns the action spec dict for a diagnosed cause. Falls back to
    manual review for any unrecognized cause, rather than guessing."""
    return ACTION_MAP.get(cause, ACTION_MAP["ambiguous"])


def map_batch_actions(diagnosed_results):
    """
    diagnosed_results: list of (event, diagnosis) tuples.

    Returns a list of (event, diagnosis, action_spec) tuples.
    """
    output = []
    for evt, diagnosis in diagnosed_results:
        action_spec = get_action_for_cause(diagnosis["predicted_cause"])
        output.append((evt, diagnosis, action_spec))
    return output
