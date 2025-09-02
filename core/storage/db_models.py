class Feedback(SQLModel, table=True):
    __tablename__ = "feedbacks"

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(PGUUID(as_uuid=True), primary_key=True, nullable=False),
    )
    run_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("runs.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    node_id: uuid.UUID = Field(
        sa_column=Column(
            PGUUID(as_uuid=True),
            ForeignKey("nodes.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        )
    )
    source: str = Field(sa_column=Column(String, nullable=False))
    # Choix “large” : reviewer optionnel (main) mais compatible avec tests qui le renseignent.
    reviewer: Optional[str] = Field(default=None, sa_column=Column(String, nullable=True))
    # Score optionnel (compat tests & auto)
    score: Optional[int] = Field(default=None, sa_column=Column(Integer, nullable=True))
    # Comment optionnel
    comment: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    # Métadonnées (héritage main)
    meta: Optional[Dict] = Field(default=None, sa_column=Column("metadata", JSON, nullable=True))
    # NOUVEAU : évaluation structurée (JSON)
    evaluation: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON, nullable=True))
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
