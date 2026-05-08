"""Initial migration - create documents and extraction_logs tables

Revision ID: 001_initial
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'documents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('original_filename', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(512), nullable=False),
        sa.Column('file_size', sa.Integer()),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('doc_type', sa.String(50), nullable=False, server_default='unknown'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('raw_ocr_text', sa.Text()),
        sa.Column('extracted_data', sa.JSON()),
        sa.Column('confidence_score', sa.Float()),
        sa.Column('error_message', sa.Text()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_documents_id', 'documents', ['id'])

    op.create_table(
        'extraction_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('stage', sa.String(50)),
        sa.Column('message', sa.Text()),
        sa.Column('level', sa.String(20), server_default='info'),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('extraction_logs')
    op.drop_table('documents')
