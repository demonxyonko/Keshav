import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATABASE_PATH = (
    PROJECT_ROOT
    / "data"
    / "keshav_chats.db"
)

ATTACHMENT_STORAGE_ROOT = (
    PROJECT_ROOT
    / "data"
    / "chat_attachments"
)


class ChatStore:
    def __init__(
        self,
        database_path: Path = DATABASE_PATH,
    ) -> None:
        self.database_path = database_path

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        ATTACHMENT_STORAGE_ROOT.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._lock = threading.RLock()

        self._initialize_database()

    # ======================================================
    # Database connection
    # ======================================================

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.database_path,
            check_same_thread=False,
            timeout=5,
        )

        connection.row_factory = sqlite3.Row

        connection.execute(
            "PRAGMA foreign_keys = ON"
        )

        connection.execute(
            "PRAGMA busy_timeout = 5000"
        )

        return connection

    # ======================================================
    # Database setup / migration
    # ======================================================

    @staticmethod
    def _table_columns(
        connection: sqlite3.Connection,
        table_name: str,
    ) -> set[str]:
        rows = connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return {
            str(row["name"])
            for row in rows
        }

    def _initialize_database(self) -> None:
        with self._lock:
            with self._connect() as connection:

                connection.execute(
                    "PRAGMA journal_mode = WAL"
                )

                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )

                connection.execute(
                    """
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        model_content TEXT,
                        attachments_json TEXT NOT NULL DEFAULT '[]',
                        created_at TEXT NOT NULL,

                        FOREIGN KEY (conversation_id)
                            REFERENCES conversations(id)
                            ON DELETE CASCADE
                    )
                    """
                )

                # Safe migration for databases created by
                # earlier Keshav versions.
                message_columns = self._table_columns(
                    connection,
                    "messages",
                )

                if "model_content" not in message_columns:
                    connection.execute(
                        """
                        ALTER TABLE messages
                        ADD COLUMN model_content TEXT
                        """
                    )

                if "attachments_json" not in message_columns:
                    connection.execute(
                        """
                        ALTER TABLE messages
                        ADD COLUMN attachments_json
                        TEXT NOT NULL DEFAULT '[]'
                        """
                    )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_messages_conversation_id
                    ON messages(conversation_id)
                    """
                )

                connection.execute(
                    """
                    CREATE INDEX IF NOT EXISTS
                    idx_conversations_updated_at
                    ON conversations(updated_at)
                    """
                )

    # ======================================================
    # Time helper
    # ======================================================

    @staticmethod
    def _now() -> str:
        return datetime.now(
            timezone.utc
        ).isoformat()

    # ======================================================
    # Attachment helpers
    # ======================================================

    @staticmethod
    def _serialize_attachments(
        attachments: list[dict] | None,
    ) -> str:
        safe_attachments = (
            attachments
            if isinstance(attachments, list)
            else []
        )

        return json.dumps(
            safe_attachments,
            ensure_ascii=False,
        )

    @staticmethod
    def _deserialize_attachments(
        raw_value: str | None,
    ) -> list[dict]:
        if not raw_value:
            return []

        try:
            value = json.loads(raw_value)
        except (TypeError, json.JSONDecodeError):
            return []

        if not isinstance(value, list):
            return []

        return [
            item
            for item in value
            if isinstance(item, dict)
        ]

    @staticmethod
    def _is_managed_attachment_path(
        file_path: Path,
    ) -> bool:
        try:
            file_path.resolve().relative_to(
                ATTACHMENT_STORAGE_ROOT.resolve()
            )
            return True
        except (OSError, ValueError):
            return False

    def _delete_managed_attachments(
        self,
        attachment_groups: list[list[dict]],
    ) -> None:
        parent_directories: set[Path] = set()

        for attachments in attachment_groups:
            for attachment in attachments:
                if not attachment.get(
                    "managed_copy",
                    False,
                ):
                    continue

                stored_path = attachment.get(
                    "stored_path"
                )

                if not stored_path:
                    continue

                path = Path(str(stored_path))

                if not self._is_managed_attachment_path(
                    path
                ):
                    continue

                try:
                    path.unlink(
                        missing_ok=True
                    )
                    parent_directories.add(
                        path.parent
                    )
                except OSError:
                    pass

        # Remove now-empty per-conversation folders.
        for directory in sorted(
            parent_directories,
            key=lambda item: len(item.parts),
            reverse=True,
        ):
            try:
                directory.rmdir()
            except OSError:
                pass

    # ======================================================
    # Create conversation
    # ======================================================

    def create_conversation(
        self,
        title: str = "New Chat",
    ) -> str:
        conversation_id = uuid4().hex
        now = self._now()

        clean_title = (
            title.strip()
            if title and title.strip()
            else "New Chat"
        )

        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO conversations (
                        id,
                        title,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        clean_title,
                        now,
                        now,
                    ),
                )

        return conversation_id

    # ======================================================
    # Conversation checks
    # ======================================================

    def conversation_exists(
        self,
        conversation_id: str,
    ) -> bool:
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT id
                    FROM conversations
                    WHERE id = ?
                    """,
                    (conversation_id,),
                ).fetchone()

        return row is not None

    def get_message_count(
        self,
        conversation_id: str,
    ) -> int:
        with self._lock:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT COUNT(*) AS message_count
                    FROM messages
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,),
                ).fetchone()

        if row is None:
            return 0

        return int(
            row["message_count"]
        )

    def is_conversation_empty(
        self,
        conversation_id: str,
    ) -> bool:
        return (
            self.get_message_count(
                conversation_id
            )
            == 0
        )

    # ======================================================
    # Add message
    # ======================================================

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        model_content: str | None = None,
        attachments: list[dict] | None = None,
    ) -> int:
        """
        Store display content separately from hidden model
        context and attachment metadata.

        Existing callers can continue passing only the original
        three arguments.
        """

        allowed_roles = {
            "user",
            "assistant",
            "system",
        }

        if role not in allowed_roles:
            raise ValueError(
                f"Unsupported message role: {role}"
            )

        if not self.conversation_exists(
            conversation_id
        ):
            raise ValueError(
                "Conversation does not exist."
            )

        now = self._now()
        attachment_json = (
            self._serialize_attachments(
                attachments
            )
        )

        with self._lock:
            with self._connect() as connection:
                cursor = connection.execute(
                    """
                    INSERT INTO messages (
                        conversation_id,
                        role,
                        content,
                        model_content,
                        attachments_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        conversation_id,
                        role,
                        content,
                        model_content,
                        attachment_json,
                        now,
                    ),
                )

                connection.execute(
                    """
                    UPDATE conversations
                    SET updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        now,
                        conversation_id,
                    ),
                )

                message_id = int(
                    cursor.lastrowid
                )

        return message_id

    # ======================================================
    # Read messages
    # ======================================================

    def get_messages(
        self,
        conversation_id: str,
    ) -> list[dict]:
        with self._lock:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT
                        id,
                        role,
                        content,
                        model_content,
                        attachments_json,
                        created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY id ASC
                    """,
                    (conversation_id,),
                ).fetchall()

        return [
            {
                "id": int(row["id"]),
                "role": row["role"],
                "content": row["content"],
                "model_content": (
                    row["model_content"]
                    or row["content"]
                ),
                "attachments": (
                    self._deserialize_attachments(
                        row["attachments_json"]
                    )
                ),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    # ======================================================
    # List conversations
    # ======================================================

    def list_conversations(
        self,
        include_empty: bool = True,
    ) -> list[dict]:
        query = """
            SELECT
                conversations.id,
                conversations.title,
                conversations.created_at,
                conversations.updated_at,
                COUNT(messages.id) AS message_count

            FROM conversations

            LEFT JOIN messages
                ON messages.conversation_id
                = conversations.id

            GROUP BY
                conversations.id,
                conversations.title,
                conversations.created_at,
                conversations.updated_at
        """

        if not include_empty:
            query += """
                HAVING COUNT(messages.id) > 0
            """

        query += """
            ORDER BY conversations.updated_at DESC
        """

        with self._lock:
            with self._connect() as connection:
                rows = connection.execute(
                    query
                ).fetchall()

        return [
            {
                "id": row["id"],
                "title": row["title"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "message_count": int(
                    row["message_count"]
                ),
            }
            for row in rows
        ]

    # ======================================================
    # Rename conversation
    # ======================================================

    def rename_conversation(
        self,
        conversation_id: str,
        title: str,
    ) -> None:
        clean_title = (
            title.strip()
            if title and title.strip()
            else "New Chat"
        )

        with self._lock:
            with self._connect() as connection:
                connection.execute(
                    """
                    UPDATE conversations
                    SET
                        title = ?,
                        updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        clean_title,
                        self._now(),
                        conversation_id,
                    ),
                )

    # ======================================================
    # Delete one conversation
    # ======================================================

    def delete_conversation(
        self,
        conversation_id: str,
    ) -> None:
        attachment_groups: list[
            list[dict]
        ] = []

        with self._lock:
            with self._connect() as connection:
                rows = connection.execute(
                    """
                    SELECT attachments_json
                    FROM messages
                    WHERE conversation_id = ?
                    """,
                    (conversation_id,),
                ).fetchall()

                attachment_groups = [
                    self._deserialize_attachments(
                        row["attachments_json"]
                    )
                    for row in rows
                ]

                connection.execute(
                    """
                    DELETE FROM conversations
                    WHERE id = ?
                    """,
                    (conversation_id,),
                )

        self._delete_managed_attachments(
            attachment_groups
        )

    # ======================================================
    # Delete unused empty conversations
    # ======================================================

    def delete_empty_conversations(
        self,
        exclude_conversation_id: str | None = None,
    ) -> int:
        """
        Delete conversations that contain no messages.

        The currently active conversation can be excluded so
        it remains available while the user is typing.
        """

        query = """
            DELETE FROM conversations

            WHERE NOT EXISTS (
                SELECT 1
                FROM messages
                WHERE messages.conversation_id
                    = conversations.id
            )
        """

        parameters: tuple = ()

        if exclude_conversation_id:
            query += """
                AND conversations.id != ?
            """

            parameters = (
                exclude_conversation_id,
            )

        with self._lock:
            with self._connect() as connection:
                cursor = connection.execute(
                    query,
                    parameters,
                )

                deleted_count = cursor.rowcount

        return max(
            0,
            deleted_count,
        )


chat_store = ChatStore()
