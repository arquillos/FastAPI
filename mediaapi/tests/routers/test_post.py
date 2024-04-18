import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.fixture()
async def created_comment(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/comment",
        json={"body": "Test comment", "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


async def create_post(async_client: AsyncClient, logged_in_token: str, post_body: str):
    await async_client.post(
        "/post",
        json={"body": post_body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )


@pytest.mark.anyio
async def test_create_post(
    async_client: AsyncClient, confirmed_user: dict, logged_in_token: str
):
    # Arrange
    body = "Test post"

    # Act
    response = await async_client.post(
        "/post",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert "application/json" == response.headers.get("content-type")
    assert {
        "id": 1,
        "body": body,
        "user_id": confirmed_user["id"],
    } == response.json()  # SqlAlchemy - Ids starts with value: 1


@pytest.mark.anyio
async def test_create_post_with_unpexpected_method(async_client: AsyncClient):
    # Arrange
    body = "Test post"

    # Act
    response = await async_client.put(
        "/post",
        json={"body": body},
    )

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.anyio
async def test_create_post_without_a_body(
    async_client: AsyncClient, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/post",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_post_with_wrong_body(
    async_client: AsyncClient, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/post",
        json={"body": 123},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_post_with_unexpected_body(
    async_client: AsyncClient, registered_user: dict, logged_in_token: str
):
    # Arrange
    body = "Test post"

    # Act
    response = await async_client.post(
        "/post",
        json={"body": body, "unexpected": True},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert "application/json" == response.headers.get("content-type")
    assert {
        "id": 1,
        "body": body,
        "user_id": registered_user["id"],
    } == response.json()


@pytest.mark.anyio
async def test_create_post_with_wrong_url(
    async_client: AsyncClient, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/posts",
        json={"body": 123},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.anyio
async def test_get_all_posts(async_client: AsyncClient, created_post: dict):
    """Check getting all the existing posts"""
    # Act
    response = await async_client.get("/post")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [{**created_post, "likes": 0}]


@pytest.mark.anyio
async def test_get_all_posts_no_existing_posts(async_client: AsyncClient):
    """Check getting all posts when there is none"""
    # Act
    response = await async_client.get("/post")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []

 
@pytest.mark.anyio
async def test_get_all_posts_with_unpexpected_method(async_client: AsyncClient):
    """Check getting all the posts with an unsupported method"""
    # Act
    response = await async_client.put("/post", json={"body": "Unexpected method"})

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.anyio
@pytest.mark.parametrize(
    "sorting, expected_order", 
    [
        ("new", [2, 1]),
        ("old", [1, 2])
    ]
)
async def test_get_all_post_sorted(
    async_client: AsyncClient, logged_in_token: str, sorting: str, expected_order: list[int]
    ):
    """Check the sorting methods for the method"""
    # Arrange: We need at leas two posts
    await create_post(async_client, logged_in_token, "Test post 1")
    await create_post(async_client, logged_in_token, "Test post 2")

    # Act
    response = await async_client.get("/post", params={"sorting": sorting})
    data = response.json()
    post_ids = [post["id"] for post in data]

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert expected_order == post_ids


@pytest.mark.anyio
async def test_get_all_post_sorted_by_likes(
    async_client: AsyncClient, logged_in_token: str
    ):
    """Check the sorting by likes method"""
    # Arrange: We need at leas two posts
    await create_post(async_client, logged_in_token, "Test post 1")
    await create_post(async_client, logged_in_token, "Test post 2")
    await async_client.post(
        "/like",
        json={"post_id": "1"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    expected_order = [1, 2]

    # Act
    response = await async_client.get("/post", params={"sorting": "most_likes"})
    data = response.json()
    post_ids = [post["id"] for post in data]

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert expected_order == post_ids



@pytest.mark.anyio
async def test_get_all_post_sorted_by_no_existent_method(async_client: AsyncClient):
    """Check a non existing sorting method"""
    # Act
    response = await async_client.get("/post", params={"sorting": "wrong_value"})

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_comment(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    """Check creating a new comment"""
    # Arrange
    body = "Test comment"

    # Act
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": registered_user["id"],
    } == response.json()


@pytest.mark.anyio
async def test_create_comment_with_unexpected_method(
    async_client: AsyncClient, created_post: dict
):
    """Check creating a new comment with an unsupported method"""
    # Arrange
    body = "Test comment"

    # Act
    response = await async_client.put(
        "/comment", json={"body": body, "post_id": created_post["id"]}
    )

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.anyio
async def test_create_comment_without_a_body(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Check creating a new comment without a body"""
    # Act
    response = await async_client.post(
        "/comment",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_comment_with_missing_post_id(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Check creating a new comment without post Id"""
    # Arrange
    body = "Test comment"

    # Act
    response = await async_client.post(
        "/comment",
        json={"body": body},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_comment_with_wrong_body(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    """Check creating a new comment with a wrong body"""
    # Act
    response = await async_client.post(
        "/comment",
        json={"body": 123, "post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_create_comment_with_unexpected_body(
    async_client: AsyncClient,
    created_post: dict,
    registered_user: dict,
    logged_in_token: str,
):
    """Check creating a new comment with an unexpected body"""
    # Arrange
    body = "Test comment"

    # Act
    response = await async_client.post(
        "/comment",
        json={"body": body, "post_id": created_post["id"], "Unexpected": "42"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert {
        "id": 1,
        "body": body,
        "post_id": created_post["id"],
        "user_id": registered_user["id"],
    } == response.json()


@pytest.mark.anyio
async def test_get_comments_on_post(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Check getting the commentos of a post"""
    # Act
    response = await async_client.get(f"/post/{created_post['id']}/comments")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == [created_comment]


@pytest.mark.anyio
async def test_get_comments_on_post_with_no_comments(
    async_client: AsyncClient, created_post: dict
):
    """Check getting the comments of a post with no comments"""
    # Act
    response = await async_client.get(f"/post/{created_post['id']}/comments")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.anyio
async def test_get_comments_on_post_with_unexpected_method(
    async_client: AsyncClient, created_post: dict
):
    """Check getting the comments of a post with an unsupported method"""
    # Act
    response = await async_client.post(f"/post/{created_post['id']}/comments")

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.anyio
async def test_get_comments_on_post_with_unexpected_post_id(async_client: AsyncClient):
    """Check getting a the comments of a un-existent post"""
    # Act
    response = await async_client.get("/post/42/comments")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


@pytest.mark.anyio
async def test_get_post_with_comments(
    async_client: AsyncClient, created_post: dict, created_comment: dict
):
    """Check getting a post with the comments"""
    # Act
    response = await async_client.get(f"/post/{created_post['id']}")

    # Assert
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "post": {**created_post, "likes": 0}, 
        "comments": [created_comment],
        }


@pytest.mark.anyio
async def test_get_post_with_comments_unexpected_method(
    async_client: AsyncClient, created_post: dict
):
    """Check getting a post with an unsupported method"""
    # Act
    response = await async_client.post(f"/post/{created_post['id']}")

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.anyio
async def test_get_post_with_comments_with_non_existent_post(async_client: AsyncClient):
    """Check getting a non-existent post"""
    # Act
    response = await async_client.get("/post/42")

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
