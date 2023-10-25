from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import ExtendedUserSchema, UserSchema
from backend.services.other_services import (
    get_full_name,
    get_user,
    get_user_with_following,
    get_user_with_following_and_followers,
)


async def add_follow_user_db(
    session: AsyncSession,
    user_id: int,
    follow_user_id: int,
) -> None:
    """
    Добавление подписки на пользователя.

    :raise ValueError: Если пользователь не найден.
    """
    current_user = await get_user_with_following(session, user_id)
    follow_user = await get_user(session, follow_user_id)

    current_user.following.append(follow_user)
    await session.commit()


async def delete_follow_user_db(
    session: AsyncSession,
    user_id: int,
    follow_user_id: int,
) -> None:
    """
    Удаление подписки на пользователя.

    :raise ValueError: Если пользователь не найден или если его нет в подписках.
    """
    current_user = await get_user_with_following(session, user_id)
    follow_user = await get_user(session, follow_user_id)

    if follow_user in current_user.following:
        current_user.following.remove(follow_user)
        await session.commit()
        return
    raise ValueError("No user subscription")


async def serialize_user_extended(
    session: AsyncSession,
    user_id: int,
) -> ExtendedUserSchema:
    """
    Сериализация расширенной информации о юзере.

    :raise ValueError: Если пользователь не найден.
    """
    user = await get_user_with_following_and_followers(session, user_id)

    return ExtendedUserSchema(
        id=user.id,
        name=get_full_name(user),
        followers=[
            UserSchema(id=follower.id, name=get_full_name(follower))
            for follower in user.followers
        ],
        following=[
            UserSchema(id=following.id, name=get_full_name(following))
            for following in user.following
        ],
    )
