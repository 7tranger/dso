from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from src.adapters.db import get_db
from src.adapters.models import Board, User
from src.domain.schemas import (
    ApiErrorPayload,
    BoardCreate,
    BoardOut,
    CardCreate,
    CardMove,
    CardOut,
    CardUpdate,
    ScoreRequest,
    ScoreResponse,
    Token,
    UserCreate,
    UserOut,
)
from src.services import auth as auth_svc
from src.services.cards import (
    create_card,
    delete_card,
    get_card,
    list_cards,
    move_card,
    to_card_out,
    to_cards_out,
    update_card,
)
from src.services.external import fetch_score_or_raise

router = APIRouter(prefix="/api/v1")


def _wrap_error(code: str, message: str, status_code: int) -> HTTPException:
    payload = ApiErrorPayload(code=code, message=message, details={})
    return HTTPException(status_code=status_code, detail=payload.model_dump())


@router.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    user = auth_svc.create_user(db, data)
    return user


@router.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = auth_svc.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise _wrap_error(
            code="INVALID_CREDENTIALS",
            message="Incorrect email or password",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    return auth_svc.issue_token_for_user(user)


@router.post("/auth/logout")
def logout():
    # For stateless JWT logout is handled on the client side.
    return {"message": "Logged out"}


@router.post("/boards", response_model=BoardOut, status_code=status.HTTP_201_CREATED)
def create_board(
    data: BoardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    board = Board(title=data.title, owner_id=current_user.id)
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


@router.get("/boards", response_model=list[BoardOut])
def list_boards(
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    q = db.query(Board)
    if current_user.role != "admin":
        q = q.filter(Board.owner_id == current_user.id)
    boards = q.order_by(Board.id.asc()).all()
    return boards


@router.post("/cards", response_model=CardOut, status_code=status.HTTP_201_CREATED)
def create_card_endpoint(
    data: CardCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    card = create_card(db, current_user, data)
    return to_card_out(card)


@router.get("/cards/{card_id}", response_model=CardOut)
def get_card_endpoint(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    card = get_card(db, card_id, current_user)
    return to_card_out(card)


@router.get("/cards", response_model=list[CardOut])
def list_cards_endpoint(
    limit: int = 20,
    offset: int = 0,
    column: str | None = None,
    board_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    cards = list_cards(
        db=db,
        requester=current_user,
        limit=limit,
        offset=offset,
        column=column,
        board_id=board_id,
    )
    return to_cards_out(list(cards))


@router.patch("/cards/{card_id}", response_model=CardOut)
def update_card_endpoint(
    card_id: int,
    data: CardUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    card = update_card(db, card_id, current_user, data)
    return to_card_out(card)


@router.delete("/cards/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_card_endpoint(
    card_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    delete_card(db, card_id, current_user)
    return


@router.patch("/cards/{card_id}/move", response_model=CardOut)
def move_card_endpoint(
    card_id: int,
    data: CardMove,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    card = move_card(db, card_id, current_user, data)
    return to_card_out(card)


@router.post("/cards/{card_id}/score", response_model=ScoreResponse)
def score_card_endpoint(
    card_id: int,
    data: ScoreRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(auth_svc.get_current_active_user),
):
    card = get_card(db, card_id, current_user)
    payload = {
        "title": card.title,
        "column": card.column,
        "estimate_hours": float(card.estimate_hours) if card.estimate_hours is not None else None,
        "due_date": card.due_date.isoformat() if card.due_date else None,
        "context": data.context,
    }
    score = fetch_score_or_raise(payload)
    return ScoreResponse(score=score)


