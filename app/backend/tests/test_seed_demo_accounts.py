"""`db.seed.seed_demo_accounts` idempotency and AC4 (exactly 2 distinct
demo accounts, one per persona, with independently generated password
hashes)."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from db.models import User
from db.seed import seed_demo_accounts


def test_seed_demo_accounts_creates_exactly_two_accounts(db_session: Session) -> None:
    created = seed_demo_accounts(db_session)

    assert created == 2
    users = db_session.execute(select(User)).scalars().all()
    assert len(users) == 2


def test_seeded_accounts_have_distinct_emails_and_personas(db_session: Session) -> None:
    seed_demo_accounts(db_session)

    users = db_session.execute(select(User)).scalars().all()
    emails = {user.email for user in users}
    personas = {user.persona for user in users}

    assert len(emails) == 2
    assert personas == {"kitchen_manager", "fb_manager"}


def test_seeded_accounts_have_independently_generated_password_hashes(
    db_session: Session,
) -> None:
    seed_demo_accounts(db_session)

    users = db_session.execute(select(User)).scalars().all()
    hashes = [user.password_hash for user in users]

    assert len(hashes) == len(set(hashes))


def test_running_seed_twice_is_idempotent_and_creates_no_duplicates(db_session: Session) -> None:
    first_run_created = seed_demo_accounts(db_session)
    second_run_created = seed_demo_accounts(db_session)

    assert first_run_created == 2
    assert second_run_created == 0

    users = db_session.execute(select(User)).scalars().all()
    assert len(users) == 2


def test_running_seed_twice_does_not_change_an_existing_accounts_password_hash(
    db_session: Session,
) -> None:
    seed_demo_accounts(db_session)
    users_after_first_run = {
        user.email: user.password_hash for user in db_session.execute(select(User)).scalars().all()
    }

    seed_demo_accounts(db_session)
    users_after_second_run = {
        user.email: user.password_hash for user in db_session.execute(select(User)).scalars().all()
    }

    assert users_after_first_run == users_after_second_run


def test_seeding_when_only_one_demo_account_already_exists_creates_only_the_missing_one(
    db_session: Session,
) -> None:
    """Idempotency must hold per-account, not just for the all-or-nothing
    case. This simulates a partial prior run (e.g. a process interrupted
    after creating one account, or a re-run against a DB where only one
    demo account was manually removed): the existing account must be left
    untouched and exactly the missing one must be (re-)created."""
    first_created = seed_demo_accounts(db_session)
    assert first_created == 2

    users = db_session.execute(select(User)).scalars().all()
    fb_manager = next(user for user in users if user.persona == "fb_manager")
    original_kitchen_manager_hash = next(
        user.password_hash for user in users if user.persona == "kitchen_manager"
    )
    db_session.delete(fb_manager)
    db_session.commit()

    remaining = db_session.execute(select(User)).scalars().all()
    assert len(remaining) == 1

    second_created = seed_demo_accounts(db_session)

    assert second_created == 1
    users_after = db_session.execute(select(User)).scalars().all()
    personas = {user.persona for user in users_after}
    assert personas == {"kitchen_manager", "fb_manager"}
    assert len(users_after) == 2
    kitchen_manager_hash_after = next(
        user.password_hash for user in users_after if user.persona == "kitchen_manager"
    )
    assert kitchen_manager_hash_after == original_kitchen_manager_hash
