# app/api/services/tags_services.py
from app.api.repositories.tags_repositories import TagRepository, get_tag_repository
from app.schemas.models.tags_models import Tag
from app.schemas.contracts.tags_dtos import TagCreate
from fastapi import Depends, HTTPException, status

class TagService:
    def __init__(self, tag_repo: TagRepository):
        self.tag_repo = tag_repo

    async def get_user_tags(self, user_id: int) -> list[Tag]:
        return await self.tag_repo.get_tags_by_user(user_id)

    async def get_user_tag_by_id(self, user_id: int, tag_id: int) -> Tag:
        tag = await self.tag_repo.get_tag_by_id_and_user(tag_id, user_id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        return tag

    async def create_tag_for_user(self, user_id: int, tag_create: TagCreate) -> Tag:
        # Prevent duplicate tag titles per user
        existing_tag = await self.tag_repo.get_tag_by_title_and_user(
            tag_create.title, user_id
        )
        if existing_tag:
            raise HTTPException(
                status_code=400,
                detail="Tag with this title already exists for the user"
            )

        tag_data = tag_create.dict()
        tag_data['user_id'] = user_id
        tag = await self.tag_repo.create_tag(tag_data)
        await self.tag_repo.db.commit()
        await self.tag_repo.db.refresh(tag)
        return tag

    async def update_user_tag(
        self,
        user_id: int,
        tag_id: int,
        tag_update: TagCreate
    ) -> Tag:
        # Ensure the tag exists and belongs to the user
        tag = await self.get_user_tag_by_id(user_id, tag_id)

        # Check for duplicate title (excluding the current tag)
        if tag_update.title != tag.title:
            existing_tag = await self.tag_repo.get_tag_by_title_and_user(
                tag_update.title, user_id
            )
            if existing_tag:
                raise HTTPException(
                    status_code=400,
                    detail="Tag with this title already exists for the user"
                )

        tag = await self.tag_repo.update_tag(tag, tag_update.title)  # flush()
        await self.tag_repo.db.commit()
        await self.tag_repo.db.refresh(tag)
        return tag
    

    async def delete_user_tag(self, user_id: int, tag_id: int):
        tag = await self.get_user_tag_by_id(user_id, tag_id)
        await self.tag_repo.delete_tag(tag)
        await self.tag_repo.db.commit()

    async def search_user_tags(
        self,
        user_id: int,
        query: str,
        skip: int | None = None,
        limit: int | None = None
    ) -> list[Tag]:
        """
        Service method to search tags for a user with validation.

        Args:
            user_id: The ID of the user.
            query: The search term (required).

        Returns:
            A list of Tag ORM objects matching the search criteria.

        Raises:
            HTTPException: If the query is too short.
        """
        # Basic validation
        if not query or len(query.strip()) < 2: # Require at least 2 non-whitespace chars
             raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Search query must be at least 2 characters long."
            )

        # Delegate to the repository
        tags = await self.tag_repo.search_tags(
            user_id=user_id,
            query=query.strip(), 
            skip=skip, 
            limit=limit
        )
        return list(tags)

# Dependency
def get_tag_service(
    tag_repo: TagRepository = Depends(get_tag_repository)
) -> TagService:
    return TagService(tag_repo)

