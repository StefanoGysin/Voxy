"""
Tests for image upload and management routes.

Tests the complete functionality of the images API including upload,
validation, CRUD operations, and security features.
"""

from io import BytesIO
from unittest.mock import Mock, patch

import pytest
from PIL import Image as PILImage
from src.voxy_agents.api.routes.images import (
    MAX_FILE_SIZE,
    generate_storage_path,
    sanitize_filename,
    validate_image_file,
)


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication."""
    user = Mock()
    user.id = "test-user-123"
    user.email = "test@example.com"
    user.role = "authenticated"
    user.user_metadata = {}
    return user


@pytest.fixture
def sample_image_data():
    """Generate sample image data for testing."""
    # Create a simple 100x100 PNG image with enough data to pass MIN_FILE_SIZE
    img = PILImage.new("RGB", (200, 200), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="PNG")
    img_bytes.seek(0)
    data = img_bytes.getvalue()
    # Ensure it's larger than MIN_FILE_SIZE (1024)
    if len(data) < 1024:
        # Add padding to reach minimum size
        data = data + b"\x00" * (1024 - len(data) + 100)
    return data


@pytest.fixture
def sample_large_image_data():
    """Generate large image data for size testing."""
    # Create data that exceeds MAX_FILE_SIZE (10MB)
    return b"x" * (MAX_FILE_SIZE + 1000)  # 10MB + 1000 bytes


class TestFileValidation:
    """Test file validation functions."""

    def test_sanitize_filename_valid(self):
        """Test filename sanitization with valid input."""
        result = sanitize_filename("test_image.jpg")
        assert result == "test_image.jpg"

    def test_sanitize_filename_special_chars(self):
        """Test filename sanitization removes special characters."""
        result = sanitize_filename("test/../image!@#$%^&*().jpg")
        assert result == "testimage.jpg"

    def test_sanitize_filename_long_name(self):
        """Test filename sanitization truncates long names."""
        long_name = "a" * 150 + ".jpg"
        result = sanitize_filename(long_name)
        assert len(result) <= 104  # 100 chars + .jpg
        assert result.endswith(".jpg")

    def test_generate_storage_path_format(self):
        """Test storage path generation format."""
        user_id = "test-user-123"
        filename = "test.jpg"

        path = generate_storage_path(user_id, filename)

        # Should follow format: users/{user_id}/uploads/{year}/{month}/{timestamp}_{uuid}_{filename}
        assert path.startswith(f"users/{user_id}/uploads/")
        assert path.endswith("_test.jpg")

        # Check path components
        parts = path.split("/")
        assert len(parts) == 6  # users, user_id, uploads, year, month, filename
        assert parts[0] == "users"
        assert parts[1] == user_id
        assert parts[2] == "uploads"
        assert len(parts[3]) == 4  # year
        assert len(parts[4]) == 2  # month
        assert len(parts[5].split("_")) >= 3  # timestamp_uuid_filename

    @pytest.mark.asyncio
    async def test_validate_image_file_valid_png(self, sample_image_data):
        """Test validation of valid PNG file."""
        from unittest.mock import AsyncMock

        mock_file = Mock()
        mock_file.content_type = "image/png"
        mock_file.filename = "test.png"
        mock_file.read = AsyncMock(return_value=sample_image_data)
        mock_file.seek = AsyncMock(return_value=None)

        with patch("magic.from_buffer", return_value="image/png"):
            result = await validate_image_file(mock_file)

            assert result["content"] == sample_image_data
            assert result["size"] == len(sample_image_data)
            assert result["mime_type"] == "image/png"
            assert result["filename"] == "test.png"

    @pytest.mark.asyncio
    async def test_validate_image_file_invalid_content_type(self, sample_image_data):
        """Test validation fails for invalid content type."""
        from fastapi import HTTPException

        mock_file = Mock()
        mock_file.content_type = "text/plain"
        mock_file.filename = "test.txt"

        with pytest.raises(HTTPException) as exc_info:
            await validate_image_file(mock_file)

        assert "Invalid file type" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_image_file_too_large(self, sample_large_image_data):
        """Test validation fails for files too large."""
        from unittest.mock import AsyncMock

        from fastapi import HTTPException

        mock_file = Mock()
        mock_file.content_type = "image/png"
        mock_file.filename = "large.png"
        mock_file.read = AsyncMock(return_value=sample_large_image_data)
        mock_file.seek = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await validate_image_file(mock_file)

        assert "File too large" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_image_file_too_small(self):
        """Test validation fails for files too small."""
        from unittest.mock import AsyncMock

        from fastapi import HTTPException

        small_data = b"small"  # Less than MIN_FILE_SIZE

        mock_file = Mock()
        mock_file.content_type = "image/png"
        mock_file.filename = "small.png"
        mock_file.read = AsyncMock(return_value=small_data)
        mock_file.seek = AsyncMock(return_value=None)

        with pytest.raises(HTTPException) as exc_info:
            await validate_image_file(mock_file)

        assert "File too small" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_validate_image_file_magic_number_mismatch(self, sample_image_data):
        """Test validation fails when magic number doesn't match content type."""
        from unittest.mock import AsyncMock

        from fastapi import HTTPException

        mock_file = Mock()
        mock_file.content_type = "image/png"
        mock_file.filename = "fake.png"
        mock_file.read = AsyncMock(return_value=sample_image_data)
        mock_file.seek = AsyncMock(return_value=None)

        # Mock magic to return different type than header
        with patch("magic.from_buffer", return_value="text/plain"):
            with pytest.raises(HTTPException) as exc_info:
                await validate_image_file(mock_file)

            assert "Invalid file format detected" in str(exc_info.value.detail)


class TestImageUploadEndpoint:
    """Test image upload endpoint."""

    @pytest.mark.asyncio
    async def test_upload_image_success(self, sample_image_data, mock_current_user):
        """Test successful image upload."""
        # Mock Supabase client and operations
        mock_supabase = Mock()
        mock_storage = Mock()
        mock_table = Mock()

        # Mock storage upload
        mock_upload_result = Mock()
        mock_upload_result.status_code = 200
        mock_storage.from_().upload.return_value = mock_upload_result
        mock_storage.from_().get_public_url.return_value = (
            "https://example.com/image.png"
        )

        # Mock database insert
        mock_insert_result = Mock()
        mock_insert_result.data = [
            {
                "id": "img-123",
                "user_id": "test-user-123",
                "storage_path": "users/test-user-123/uploads/2024/01/test.png",
                "original_name": "test.png",
                "content_type": "image/png",
                "file_size": len(sample_image_data),
                "description": None,
                "tags": None,
                "is_public": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]
        mock_table.insert().execute.return_value = mock_insert_result

        mock_supabase.storage = mock_storage
        mock_supabase.table.return_value = mock_table

        # Mock file validation
        mock_validation_result = {
            "content": sample_image_data,
            "size": len(sample_image_data),
            "mime_type": "image/png",
            "filename": "test.png",
        }

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            with patch(
                "src.voxy_agents.api.routes.images.validate_image_file",
                return_value=mock_validation_result,
            ):
                with patch(
                    "src.voxy_agents.api.routes.images.generate_storage_path",
                    return_value="users/test-user-123/uploads/2024/01/test.png",
                ):
                    from src.voxy_agents.api.routes.images import upload_image

                    # Create mock UploadFile
                    mock_file = Mock()
                    mock_file.content_type = "image/png"
                    mock_file.filename = "test.png"

                    result = await upload_image(
                        file=mock_file,
                        description=None,
                        tags=None,
                        public=False,
                        current_user=mock_current_user,
                    )

                    # Verify response
                    assert result.id == "img-123"
                    assert result.file_name == "test.png"
                    assert result.content_type == "image/png"
                    assert result.file_size == len(sample_image_data)
                    assert result.public is False
                    assert result.url == "https://example.com/image.png"
                    assert result.message == "Image uploaded successfully"

    @pytest.mark.asyncio
    async def test_upload_image_with_metadata(
        self, sample_image_data, mock_current_user
    ):
        """Test image upload with metadata (description, tags, public)."""
        # Setup mocks similar to success test
        mock_supabase = Mock()
        mock_storage = Mock()
        mock_table = Mock()

        mock_upload_result = Mock()
        mock_upload_result.status_code = 200
        mock_storage.from_().upload.return_value = mock_upload_result
        mock_storage.from_().get_public_url.return_value = (
            "https://example.com/public.png"
        )

        mock_insert_result = Mock()
        mock_insert_result.data = [
            {
                "id": "img-123",
                "user_id": "test-user-123",
                "storage_path": "users/test-user-123/uploads/2024/01/public.png",
                "original_name": "public.png",
                "content_type": "image/png",
                "file_size": len(sample_image_data),
                "description": "Test image",
                "tags": ["test", "upload"],
                "is_public": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]
        mock_table.insert().execute.return_value = mock_insert_result

        mock_supabase.storage = mock_storage
        mock_supabase.table.return_value = mock_table

        mock_validation_result = {
            "content": sample_image_data,
            "size": len(sample_image_data),
            "mime_type": "image/png",
            "filename": "public.png",
        }

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            with patch(
                "src.voxy_agents.api.routes.images.validate_image_file",
                return_value=mock_validation_result,
            ):
                with patch(
                    "src.voxy_agents.api.routes.images.generate_storage_path",
                    return_value="users/test-user-123/uploads/2024/01/public.png",
                ):
                    from src.voxy_agents.api.routes.images import upload_image

                    mock_file = Mock()
                    mock_file.content_type = "image/png"
                    mock_file.filename = "public.png"

                    result = await upload_image(
                        file=mock_file,
                        description="Test image",
                        tags='["test", "upload"]',  # JSON string
                        public=True,
                        current_user=mock_current_user,
                    )

                    # Verify metadata is preserved
                    assert result.description == "Test image"
                    assert result.tags == ["test", "upload"]
                    assert result.public is True
                    assert result.public_url == "https://example.com/public.png"

    @pytest.mark.asyncio
    async def test_upload_image_storage_failure(
        self, sample_image_data, mock_current_user
    ):
        """Test handling of storage upload failure."""
        mock_supabase = Mock()
        mock_storage = Mock()

        # Mock storage failure
        mock_upload_result = Mock()
        mock_upload_result.status_code = 500
        mock_upload_result.json.return_value = {"message": "Storage error"}
        mock_storage.from_().upload.return_value = mock_upload_result

        mock_supabase.storage = mock_storage

        mock_validation_result = {
            "content": sample_image_data,
            "size": len(sample_image_data),
            "mime_type": "image/png",
            "filename": "test.png",
        }

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            with patch(
                "src.voxy_agents.api.routes.images.validate_image_file",
                return_value=mock_validation_result,
            ):
                from src.voxy_agents.api.routes.images import upload_image

                mock_file = Mock()
                mock_file.content_type = "image/png"
                mock_file.filename = "test.png"

                with pytest.raises(Exception) as exc_info:
                    await upload_image(
                        file=mock_file,
                        description=None,
                        tags=None,
                        public=False,
                        current_user=mock_current_user,
                    )

                assert "Failed to upload file" in str(exc_info.value)


class TestImageCRUDEndpoints:
    """Test CRUD operations for images."""

    @pytest.mark.asyncio
    async def test_list_images_user_only(self, mock_current_user):
        """Test listing user's own images."""
        mock_supabase = Mock()
        mock_table = Mock()

        # Mock database query result
        mock_result = Mock()
        mock_result.data = [
            {
                "id": "img-1",
                "user_id": "test-user-123",
                "storage_path": "users/test-user-123/uploads/2024/01/image1.png",
                "original_name": "image1.png",
                "content_type": "image/png",
                "file_size": 12345,
                "description": "First image",
                "tags": ["tag1"],
                "is_public": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]

        # Mock query chain
        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.overlaps.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result

        mock_table.select.return_value = mock_query
        mock_supabase.table.return_value = mock_table
        mock_supabase.storage.from_().get_public_url.return_value = (
            "https://example.com/image1.png"
        )

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import list_images

            result = await list_images(
                public_only=False,
                tags=None,
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            assert len(result) == 1
            assert result[0].id == "img-1"
            assert result[0].file_name == "image1.png"
            assert result[0].description == "First image"
            assert result[0].tags == ["tag1"]
            assert result[0].public is False

    @pytest.mark.asyncio
    async def test_list_images_with_tag_filter(self, mock_current_user):
        """Test listing images with tag filtering."""
        mock_supabase = Mock()
        mock_table = Mock()

        mock_result = Mock()
        mock_result.data = []  # No results for filtered search

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.overlaps.return_value = mock_query
        mock_query.order.return_value = mock_query
        mock_query.range.return_value = mock_query
        mock_query.execute.return_value = mock_result

        mock_table.select.return_value = mock_query
        mock_supabase.table.return_value = mock_table

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import list_images

            result = await list_images(
                public_only=False,
                tags="nonexistent,tag",
                limit=20,
                offset=0,
                current_user=mock_current_user,
            )

            assert len(result) == 0
            # Verify overlaps was called with tag list
            mock_query.overlaps.assert_called_once_with("tags", ["nonexistent", "tag"])

    @pytest.mark.asyncio
    async def test_get_image_details_success(self, mock_current_user):
        """Test getting image details for owned image."""
        mock_supabase = Mock()
        mock_table = Mock()

        mock_result = Mock()
        mock_result.data = [
            {
                "id": "img-123",
                "user_id": "test-user-123",
                "storage_path": "users/test-user-123/uploads/2024/01/image.png",
                "original_name": "image.png",
                "content_type": "image/png",
                "file_size": 12345,
                "description": "Test image",
                "tags": ["test"],
                "is_public": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result

        mock_table.select.return_value = mock_query
        mock_supabase.table.return_value = mock_table
        mock_supabase.storage.from_().get_public_url.return_value = (
            "https://example.com/image.png"
        )

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import get_image_details

            result = await get_image_details(
                image_id="img-123", current_user=mock_current_user
            )

            assert result.id == "img-123"
            assert result.file_name == "image.png"
            assert result.description == "Test image"
            assert (
                result.storage_path == "users/test-user-123/uploads/2024/01/image.png"
            )
            assert result.public_url is None  # Private image

    @pytest.mark.asyncio
    async def test_get_image_details_not_found(self, mock_current_user):
        """Test getting details for non-existent image."""
        mock_supabase = Mock()
        mock_table = Mock()

        mock_result = Mock()
        mock_result.data = []  # No results

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result

        mock_table.select.return_value = mock_query
        mock_supabase.table.return_value = mock_table

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import get_image_details

            with pytest.raises(Exception) as exc_info:
                await get_image_details(
                    image_id="nonexistent", current_user=mock_current_user
                )

            assert "Image not found" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_image_details_access_denied(self, mock_current_user):
        """Test access denied to other user's private image."""
        mock_supabase = Mock()
        mock_table = Mock()

        mock_result = Mock()
        mock_result.data = [
            {
                "id": "img-123",
                "user_id": "other-user-456",  # Different user
                "storage_path": "users/other-user-456/uploads/2024/01/private.png",
                "original_name": "private.png",
                "content_type": "image/png",
                "file_size": 12345,
                "description": "Private image",
                "tags": [],
                "is_public": False,  # Not public
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result

        mock_table.select.return_value = mock_query
        mock_supabase.table.return_value = mock_table

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import get_image_details

            with pytest.raises(Exception) as exc_info:
                await get_image_details(
                    image_id="img-123", current_user=mock_current_user
                )

            assert "Access denied" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_update_image_metadata_success(self, mock_current_user):
        """Test successful image metadata update."""
        mock_supabase = Mock()
        Mock()

        # Mock ownership check
        mock_check_result = Mock()
        mock_check_result.data = [{"user_id": "test-user-123"}]

        # Mock update result
        mock_update_result = Mock()
        mock_update_result.data = [
            {
                "id": "img-123",
                "user_id": "test-user-123",
                "storage_path": "users/test-user-123/uploads/2024/01/updated.png",
                "original_name": "updated.png",
                "content_type": "image/png",
                "file_size": 12345,
                "description": "Updated description",
                "tags": ["updated", "tag"],
                "is_public": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:01Z",
            }
        ]

        # Mock query chains
        mock_select_query = Mock()
        mock_select_query.eq.return_value = mock_select_query
        mock_select_query.execute.return_value = mock_check_result

        mock_update_query = Mock()
        mock_update_query.eq.return_value = mock_update_query
        mock_update_query.execute.return_value = mock_update_result

        mock_detail_result = Mock()
        mock_detail_result.data = [mock_update_result.data[0]]
        mock_detail_query = Mock()
        mock_detail_query.eq.return_value = mock_detail_query
        mock_detail_query.execute.return_value = mock_detail_result

        # Setup table mock to handle different query types
        def table_side_effect(table_name):
            table_mock = Mock()
            if hasattr(table_side_effect, "call_count"):
                table_side_effect.call_count += 1
            else:
                table_side_effect.call_count = 1

            if table_side_effect.call_count == 1:  # First call - ownership check
                table_mock.select.return_value = mock_select_query
            elif table_side_effect.call_count == 2:  # Second call - update
                table_mock.update.return_value = mock_update_query
            else:  # Third call - get details
                table_mock.select.return_value = mock_detail_query

            return table_mock

        mock_supabase.table.side_effect = table_side_effect
        mock_supabase.storage.from_().get_public_url.return_value = (
            "https://example.com/updated.png"
        )

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import (
                ImageMetadataUpdate,
                update_image_metadata,
            )

            update_data = ImageMetadataUpdate(
                description="Updated description", tags=["updated", "tag"], public=True
            )

            result = await update_image_metadata(
                image_id="img-123",
                update_data=update_data,
                current_user=mock_current_user,
            )

            assert result.description == "Updated description"
            assert result.tags == ["updated", "tag"]
            assert result.public is True

    @pytest.mark.asyncio
    async def test_delete_image_success(self, mock_current_user):
        """Test successful image deletion."""
        mock_supabase = Mock()
        Mock()

        # Mock get image result
        mock_get_result = Mock()
        mock_get_result.data = [
            {
                "id": "img-123",
                "user_id": "test-user-123",
                "storage_path": "users/test-user-123/uploads/2024/01/delete-me.png",
                "original_name": "delete-me.png",
                "content_type": "image/png",
                "file_size": 12345,
                "description": "To be deleted",
                "tags": [],
                "is_public": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]

        # Mock delete result
        mock_delete_result = Mock()
        mock_delete_result.data = [{"id": "img-123"}]

        # Mock queries
        mock_get_query = Mock()
        mock_get_query.eq.return_value = mock_get_query
        mock_get_query.execute.return_value = mock_get_result

        mock_delete_query = Mock()
        mock_delete_query.eq.return_value = mock_delete_query
        mock_delete_query.execute.return_value = mock_delete_result

        # Setup table mock
        def table_side_effect(table_name):
            table_mock = Mock()
            if hasattr(table_side_effect, "call_count"):
                table_side_effect.call_count += 1
            else:
                table_side_effect.call_count = 1

            if table_side_effect.call_count == 1:  # First call - get image
                table_mock.select.return_value = mock_get_query
            else:  # Second call - delete
                table_mock.delete.return_value = mock_delete_query

            return table_mock

        mock_supabase.table.side_effect = table_side_effect

        # Mock storage deletion
        mock_storage_result = Mock()
        mock_supabase.storage.from_().remove.return_value = mock_storage_result

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import delete_image

            result = await delete_image(
                image_id="img-123", current_user=mock_current_user
            )

            assert result["message"] == "Image deleted successfully"
            assert result["image_id"] == "img-123"
            assert result["filename"] == "delete-me.png"

            # Verify storage removal was called
            mock_supabase.storage.from_().remove.assert_called_once_with(
                ["users/test-user-123/uploads/2024/01/delete-me.png"]
            )

    @pytest.mark.asyncio
    async def test_delete_image_not_owner(self, mock_current_user):
        """Test delete fails when user doesn't own image."""
        mock_supabase = Mock()
        mock_table = Mock()

        mock_result = Mock()
        mock_result.data = [
            {
                "id": "img-123",
                "user_id": "other-user-456",  # Different user
                "storage_path": "users/other-user-456/uploads/2024/01/not-mine.png",
                "original_name": "not-mine.png",
                "content_type": "image/png",
                "file_size": 12345,
                "description": "Not my image",
                "tags": [],
                "is_public": False,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-01T12:00:00Z",
            }
        ]

        mock_query = Mock()
        mock_query.eq.return_value = mock_query
        mock_query.execute.return_value = mock_result

        mock_table.select.return_value = mock_query
        mock_supabase.table.return_value = mock_table

        with patch(
            "src.voxy_agents.api.routes.images.get_supabase_client",
            return_value=mock_supabase,
        ):
            from src.voxy_agents.api.routes.images import delete_image

            with pytest.raises(Exception) as exc_info:
                await delete_image(image_id="img-123", current_user=mock_current_user)

            assert "You can only delete your own images" in str(exc_info.value)


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_image_upload_request_validation(self):
        """Test ImageUploadRequest validation."""
        from src.voxy_agents.api.routes.images import ImageUploadRequest

        # Valid request
        request = ImageUploadRequest(
            description="Test image", tags=["test", "upload"], public=True
        )
        assert request.description == "Test image"
        assert request.tags == ["test", "upload"]
        assert request.public is True

    def test_image_upload_request_tags_validation(self):
        """Test tag validation in ImageUploadRequest."""
        from src.voxy_agents.api.routes.images import ImageUploadRequest

        # Too many tags
        with pytest.raises(ValueError) as exc_info:
            ImageUploadRequest(tags=["tag"] * 15)
        assert "Maximum of 10 tags allowed" in str(exc_info.value)

        # Tags with whitespace (should be cleaned)
        request = ImageUploadRequest(tags=["  TEST  ", "", "upload "])
        assert request.tags == ["test", "upload"]

    def test_image_metadata_update_validation(self):
        """Test ImageMetadataUpdate validation."""
        from src.voxy_agents.api.routes.images import ImageMetadataUpdate

        # Partial update
        update = ImageMetadataUpdate(description="New description")
        assert update.description == "New description"
        assert update.tags is None
        assert update.public is None

        # All fields update
        update = ImageMetadataUpdate(
            description="Updated", tags=["new", "tags"], public=True
        )
        assert update.description == "Updated"
        assert update.tags == ["new", "tags"]
        assert update.public is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
