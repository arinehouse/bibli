from fastapi.testclient import TestClient
from sqlmodel import Session

from resources.strings import NOT_FOUND_ERROR


def test_get_book(client: TestClient, session: Session):
    # pylint: disable=C0415
    from src.domain.books import schemas, service

    book = service.upsert_book(session, schemas.Book(title="Demon Copperhead"))

    response = client.get(f"/book/{book.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == book.id
    assert data["title"] == book.title

    response = client.get(f"/book/{book.id + 1}")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == NOT_FOUND_ERROR


def test_get_author(client: TestClient, session: Session):
    # pylint: disable=C0415
    from src.domain.books import schemas, service

    author = service.upsert_author(session, schemas.Author(name="Javier Zamora"))

    response = client.get(f"/author/{author.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == author.id
    assert data["name"] == author.name

    response = client.get(f"/author/{author.id + 1}")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == NOT_FOUND_ERROR


def test_crud_user(client: TestClient):
    # pylint: disable=C0415
    from src.domain.users import schemas

    user = schemas.User(
        name="Archer",
        tag="archer_the_good_boi",
        info="A waggin' doggo that loves Emily Dickinson and Clifford.",
    )

    response = client.get("/user/1")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == NOT_FOUND_ERROR

    response = client.put("/user", json=user.dict())
    data = response.json()

    assert response.status_code == 200
    assert data["tag"] == user.tag
    assert data["name"] == user.name
    assert data["info"] == user.info
    assert data["id"] is not None

    user.id = data["id"]  # pylint: disable=C0103
    user.tag = "archer_the_naughty_boi"

    response = client.put("/user", json=user.dict())
    data = response.json()

    assert response.status_code == 200
    assert data["tag"] == user.tag

    response = client.get(f"/user/{user.id}")
    data = response.json()

    assert response.status_code == 200
    assert data["id"] == user.id
    assert data["tag"] == user.tag
    assert data["name"] == user.name
    assert data["info"] == user.info

    response = client.delete(f"/user/{user.id}")
    assert response.status_code == 200

    response = client.get(f"/user/{user.id}")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == NOT_FOUND_ERROR

    response = client.delete(f"/user/{user.id}")
    data = response.json()

    assert response.status_code == 404
    assert data["detail"] == NOT_FOUND_ERROR


def test_crud_user_link(client: TestClient, session: Session):
    # pylint: disable=C0415
    from src.domain.users import schemas, service

    user1 = schemas.User(tag="first", name="first")
    user1 = service.upsert_user(session, user1)

    user2 = schemas.User(tag="second", name="second")
    user2 = service.upsert_user(session, user2)

    link = schemas.UserLinkPut(
        parent_id=user1.id,
        child_id=user2.id,
        type=schemas.UserLinkType.FOLLOW,
    )

    response = client.put("/users/link", json=link.dict())
    data = response.json()

    assert response.status_code == 200
    assert data["parent_id"] == link.parent_id
    assert data["child_id"] == link.child_id
    assert data["type"] == link.type

    user_filter = {
        "parent_id": user1.id,
        "type": "follow",
    }

    response = client.get("/users/linked", params=user_filter)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 1
    assert data[0]["name"] == user2.name
    assert data[0]["tag"] == user2.tag
    assert data[0]["id"] == user2.id

    response = client.delete(f"/users/link/{user1.id}/{user2.id}")
    data = response.json()

    assert response.status_code == 200
    assert data is None

    response = client.get("/users/linked", params=user_filter)
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 0
