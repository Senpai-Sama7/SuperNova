"""initial_schema

Revision ID: 23aa65fd8071
Revises: 
Create Date: 2026-02-26 00:31:50.320681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '23aa65fd8071'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial SuperNova database schema.
    
    Includes:
    - pgvector and pg_trgm extensions
    - semantic_memories table with HNSW vector index
    - procedural_memories table with HNSW vector index
    - Full-text search indexes
    - Performance indexes
    """
    # =============================================================================
    # Task 4.2.1: Create Extensions
    # =============================================================================
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    
    # =============================================================================
    # Task 4.2.2: Create semantic_memories Table
    # =============================================================================
    op.create_table(
        'semantic_memories',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.String(), nullable=True),  # Will be altered to vector(1536)
        sa.Column('category', sa.String(100), nullable=True, index=True),
        sa.Column('confidence', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('importance', sa.Float(), nullable=True, server_default='0.5', index=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True, server_default='{}'),
        sa.Column('source', sa.String(500), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_accessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Set vector type via raw SQL (Alembic doesn't have native vector type)
    op.execute("ALTER TABLE semantic_memories ALTER COLUMN embedding TYPE vector(1536) USING embedding::vector(1536)")
    
    # =============================================================================
    # Task 4.2.3: Create HNSW Index on semantic_memories.embedding
    # =============================================================================
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_memories_embedding_hnsw 
        ON semantic_memories 
        USING hnsw (embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
    """)
    
    # =============================================================================
    # Task 4.2.4: Create Additional Indexes on semantic_memories
    # =============================================================================
    # Full-text search index
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_memories_content_fts 
        ON semantic_memories 
        USING gin (to_tsvector('english', content))
    """)
    
    # User_id index (for user-scoped queries)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_memories_user_id 
        ON semantic_memories (user_id)
    """)
    
    # Importance index (for priority retrieval)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_memories_importance 
        ON semantic_memories (importance DESC)
    """)
    
    # Last accessed index (for LRU eviction)
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_memories_last_accessed 
        ON semantic_memories (last_accessed_at DESC NULLS LAST)
    """)
    
    # Category + importance composite index
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_semantic_memories_category_importance 
        ON semantic_memories (category, importance DESC)
    """)
    
    # =============================================================================
    # Task 4.2.5: Create procedural_memories Table
    # =============================================================================
    op.create_table(
        'procedural_memories',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('trigger_conditions', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('compiled_graph_bytes', sa.LargeBinary(), nullable=True),
        sa.Column('trigger_embedding', sa.String(), nullable=True),  # Will be altered to vector(1536)
        sa.Column('invocation_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('avg_performance_score', sa.Float(), nullable=True, server_default='0.5'),
        sa.Column('success_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('failure_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_invoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Set vector type
    op.execute("ALTER TABLE procedural_memories ALTER COLUMN trigger_embedding TYPE vector(1536) USING trigger_embedding::vector(1536)")
    
    # =============================================================================
    # Task 4.2.6: Create HNSW Index on procedural_memories.trigger_embedding
    # =============================================================================
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_procedural_memories_trigger_embedding_hnsw 
        ON procedural_memories 
        USING hnsw (trigger_embedding vector_cosine_ops) 
        WITH (m = 16, ef_construction = 64)
    """)
    
    # Additional indexes for procedural_memories
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_procedural_memories_name 
        ON procedural_memories (name)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_procedural_memories_is_active 
        ON procedural_memories (is_active) 
        WHERE is_active = true
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_procedural_memories_invocation_count 
        ON procedural_memories (invocation_count DESC)
    """)
    
    # GIN index on trigger_conditions for JSONB queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_procedural_memories_trigger_conditions 
        ON procedural_memories 
        USING gin (trigger_conditions)
    """)
    
    # =============================================================================
    # Create checkpoint table for LangGraph
    # =============================================================================
    op.create_table(
        'checkpoints',
        sa.Column('thread_id', sa.String(255), nullable=False),
        sa.Column('checkpoint_ns', sa.String(255), nullable=False, server_default=''),
        sa.Column('checkpoint_id', sa.String(255), nullable=False),
        sa.Column('parent_checkpoint_id', sa.String(255), nullable=True),
        sa.Column('type', sa.String(50), nullable=True),
        sa.Column('checkpoint', postgresql.JSONB(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('thread_id', 'checkpoint_ns', 'checkpoint_id')
    )
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id 
        ON checkpoints (thread_id)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at 
        ON checkpoints (created_at DESC)
    """)
    
    # =============================================================================
    # Create audit_log table (CC-14)
    # =============================================================================
    op.create_table(
        'audit_log',
        sa.Column('id', sa.UUID(), nullable=False, server_default=sa.text('gen_random_uuid()')),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('actor', sa.String(255), nullable=True),
        sa.Column('resource_type', sa.String(100), nullable=True),
        sa.Column('resource_id', sa.String(255), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True, server_default='{}'),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('correlation_id', sa.String(255), nullable=True, index=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp 
        ON audit_log (timestamp DESC)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_action 
        ON audit_log (action)
    """)
    
    op.execute("""
        CREATE INDEX IF NOT EXISTS idx_audit_log_actor 
        ON audit_log (actor)
    """)


def downgrade() -> None:
    """Drop all SuperNova tables and extensions."""
    # Drop tables in reverse order
    op.drop_table('audit_log')
    op.drop_table('checkpoints')
    op.drop_table('procedural_memories')
    op.drop_table('semantic_memories')
    
    # Drop extensions
    op.execute("DROP EXTENSION IF EXISTS pg_trgm")
    op.execute("DROP EXTENSION IF EXISTS vector")
