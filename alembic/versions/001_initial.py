"""Initial schema: users, addresses, orders, wallets, transactions.

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", sa.Enum("CUSTOMER", "SHOPPER", "ADMIN", name="userrole"), nullable=False),
        sa.Column("status", sa.Enum("ACTIVE", "SUSPENDED", "DELETED", name="userstatus"), nullable=False),
        sa.Column("email_verified", sa.Boolean(), nullable=True),
        sa.Column("phone_verified", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    op.create_table(
        "wallets",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("balance", sa.Numeric(10, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    op.create_table(
        "addresses",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("label", sa.String(50), nullable=False),
        sa.Column("recipient_name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=False),
        sa.Column("address_line1", sa.String(500), nullable=False),
        sa.Column("address_line2", sa.String(500), nullable=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("region", sa.String(100), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    order_status = postgresql.ENUM(
        "PENDING", "ASSIGNED", "PURCHASED", "SHIPPED", "DELIVERED", "CANCELLED",
        name="order_status",
        create_type=False,
    )
    order_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("shopper_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("product_url", sa.Text(), nullable=False),
        sa.Column("product_name", sa.String(500), nullable=False),
        sa.Column("variant_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("estimated_price_gbp", sa.Numeric(10, 2), nullable=False),
        sa.Column("actual_price_gbp", sa.Numeric(10, 2), nullable=True),
        sa.Column("commission_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("commission_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("shipping_cost", sa.Numeric(10, 2), nullable=True),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "ASSIGNED", "PURCHASED", "SHIPPED", "DELIVERED", "CANCELLED", name="order_status"), nullable=False),
        sa.Column("tracking_number", sa.String(100), nullable=True),
        sa.Column("delivery_address", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["shopper_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "order_status_history",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "ASSIGNED", "PURCHASED", "SHIPPED", "DELIVERED", "CANCELLED", name="order_status"), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("changed_by", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    tx_type = postgresql.ENUM("CREDIT", "DEBIT", name="transactiontype", create_type=False)
    tx_status = postgresql.ENUM("PENDING", "COMPLETED", "FAILED", "REFUNDED", name="transactionstatus", create_type=False)
    tx_type.create(op.get_bind(), checkfirst=True)
    tx_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("wallet_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("type", postgresql.ENUM("CREDIT", "DEBIT", name="transactiontype"), nullable=False),
        sa.Column("amount", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", postgresql.ENUM("PENDING", "COMPLETED", "FAILED", "REFUNDED", name="transactionstatus"), nullable=False),
        sa.Column("payment_method", sa.String(50), nullable=True),
        sa.Column("payment_reference", sa.String(100), nullable=True),
        sa.Column("description", sa.String(500), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["wallet_id"], ["wallets.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_transactions_payment_reference", "transactions", ["payment_reference"], unique=True)


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("order_status_history")
    op.drop_table("orders")
    op.drop_table("addresses")
    op.drop_table("wallets")
    op.drop_table("users")
    op.execute("DROP TYPE IF EXISTS order_status")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS userrole")
    op.execute("DROP TYPE IF EXISTS userstatus")
