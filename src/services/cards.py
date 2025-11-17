from datetime import datetime, timezone
from typing import List, Optional, Sequence

from fastapi import HTTPException, status
from sqlalchemy import asc
from sqlalchemy.orm import Session

from src.adapters.models import Board, Card, User
from src.domain.schemas import CardCreate, CardMove, CardOut, CardUpdate


def _ensure_board_for_owner(db: Session, board_id: int, owner: User) -> Board:
    board = db.get(Board, board_id)
    if board is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "BOARD_NOT_FOUND", "message": "Board not found", "details": {}},
        )
    if board.owner_id != owner.id and owner.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied", "details": {}},
        )
    return board


def create_card(db: Session, owner: User, data: CardCreate) -> Card:
    _ensure_board_for_owner(db, data.board_id, owner)

    card = Card(
        title=data.title,
        column=data.column,
        order_idx=data.order_idx,
        board_id=data.board_id,
        owner_id=owner.id,
        estimate_hours=data.estimate_hours,
        due_date=data.due_date,
    )
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def get_card(db: Session, card_id: int, requester: User) -> Card:
    card = db.get(Card, card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "CARD_NOT_FOUND", "message": "Card not found", "details": {}},
        )
    if card.owner_id != requester.id and requester.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "FORBIDDEN", "message": "Access denied", "details": {}},
        )
    return card


def list_cards(
    db: Session,
    requester: User,
    limit: int = 20,
    offset: int = 0,
    column: Optional[str] = None,
    board_id: Optional[int] = None,
) -> Sequence[Card]:
    q = db.query(Card)
    if requester.role != "admin":
        q = q.filter(Card.owner_id == requester.id)
    if column is not None:
        q = q.filter(Card.column == column)
    if board_id is not None:
        q = q.filter(Card.board_id == board_id)
    q = q.order_by(asc(Card.board_id), asc(Card.column), asc(Card.order_idx), asc(Card.id))
    return q.offset(offset).limit(limit).all()


def update_card(db: Session, card_id: int, requester: User, data: CardUpdate) -> Card:
    card = get_card(db, card_id, requester)

    if data.title is not None:
        card.title = data.title
    if data.column is not None:
        card.column = data.column
    if data.order_idx is not None:
        card.order_idx = data.order_idx
    if data.estimate_hours is not None:
        card.estimate_hours = data.estimate_hours
    if data.due_date is not None:
        card.due_date = data.due_date

    card.updated_at = datetime.now(timezone.utc)

    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def delete_card(db: Session, card_id: int, requester: User) -> None:
    card = get_card(db, card_id, requester)
    db.delete(card)
    db.commit()


def move_card(db: Session, card_id: int, requester: User, data: CardMove) -> Card:
    card = get_card(db, card_id, requester)
    card.column = data.column
    card.order_idx = data.order_idx
    card.updated_at = datetime.now(timezone.utc)
    db.add(card)
    db.commit()
    db.refresh(card)
    return card


def to_card_out(card: Card) -> CardOut:
    return CardOut.model_validate(card)


def to_cards_out(cards: List[Card]) -> List[CardOut]:
    return [to_card_out(c) for c in cards]


