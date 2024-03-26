import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.fixture()
async def created_like(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
) -> dict:
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )
    return response.json()


@pytest.mark.anyio
async def test_like_post(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert "application/json" == response.headers.get("content-type")
    assert {"id": 1, "user_id": 1, "post_id": 1} == response.json()


@pytest.mark.anyio
async def test_like_post_with_unpexpected_method(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    # Act
    response = await async_client.put(
        "/like",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED


@pytest.mark.anyio
async def test_like_post_without_a_body(
    async_client: AsyncClient, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/like",
        json={},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_like_post_with_wrong_body(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/like",
        json={"post_id": "Hello"},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.anyio
async def test_like_post_with_unexpected_body(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    # Act
    response = await async_client.post(
        "/like",
        json={"post_id": created_post["id"], "unexpected": True},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_201_CREATED
    assert "application/json" == response.headers.get("content-type")
    assert {"id": 1, "user_id": 1, "post_id": 1} == response.json()


@pytest.mark.anyio
async def test_like_post_with_wrong_url(
    async_client: AsyncClient, created_post: dict, logged_in_token: str
):
    # Act
    # Act
    response = await async_client.post(
        "/likes",
        json={"post_id": created_post["id"]},
        headers={"Authorization": f"Bearer {logged_in_token}"},
    )

    # Assert
    assert response.status_code == status.HTTP_404_NOT_FOUND
