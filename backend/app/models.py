from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class AmendmentType(str, enum.Enum):
    BUG = "Bug"
    FAULT = "Fault"
    ENHANCEMENT = "Enhancement"
    FEATURE = "Feature"
    SUGGESTION = "Suggestion"
    MAINTENANCE = "Maintenance"
    DOCUMENTATION = "Documentation"


class AmendmentStatus(str, enum.Enum):
    OPEN = "Open"
    IN_PROGRESS = "In Progress"
    TESTING = "Testing"
    COMPLETED = "Completed"
    DEPLOYED = "Deployed"


class DevelopmentStatus(str, enum.Enum):
    NOT_STARTED = "Not Started"
    IN_DEVELOPMENT = "In Development"
    CODE_REVIEW = "Code Review"
    READY_FOR_QA = "Ready for QA"


class Priority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Force(str, enum.Enum):
    ARMY = "Army"
    NAVY = "Navy"
    RAF = "RAF"
    ALL = "All"


class LinkType(str, enum.Enum):
    RELATED = "Related"
    DUPLICATE = "Duplicate"
    BLOCKS = "Blocks"
    BLOCKED_BY = "Blocked By"


class Amendment(Base):
    __tablename__ = "amendments"

    # Primary identification
    amendment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_reference = Column(String(50), unique=True, nullable=False, index=True)

    # Basic information
    amendment_type = Column(SQLEnum(AmendmentType), nullable=False)
    description = Column(Text, nullable=False)
    amendment_status = Column(
        SQLEnum(AmendmentStatus), nullable=False, default=AmendmentStatus.OPEN
    )
    development_status = Column(
        SQLEnum(DevelopmentStatus),
        nullable=False,
        default=DevelopmentStatus.NOT_STARTED,
    )
    priority = Column(SQLEnum(Priority), nullable=False, default=Priority.MEDIUM)
    force = Column(String(50), nullable=True)
    application = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    # Assignment and reporting
    reported_by = Column(String(100), nullable=True)
    assigned_to = Column(String(100), nullable=True)
    date_reported = Column(DateTime, nullable=True)

    # Development fields
    database_changes = Column(Boolean, default=False)
    db_upgrade_changes = Column(Boolean, default=False)
    release_notes = Column(Text, nullable=True)

    # QA fields
    qa_assigned_id = Column(Integer, nullable=True)
    qa_assigned_date = Column(DateTime, nullable=True)
    qa_test_plan_check = Column(Boolean, default=False)
    qa_test_release_notes_check = Column(Boolean, default=False)
    qa_completed = Column(Boolean, default=False)
    qa_signature = Column(String(100), nullable=True)
    qa_completed_date = Column(DateTime, nullable=True)
    qa_notes = Column(Text, nullable=True)
    qa_test_plan_link = Column(String(500), nullable=True)

    # Audit fields
    created_by = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_by = Column(String(100), nullable=True)
    modified_on = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    progress_entries = relationship(
        "AmendmentProgress", back_populates="amendment", cascade="all, delete-orphan"
    )
    applications = relationship(
        "AmendmentApplication", back_populates="amendment", cascade="all, delete-orphan"
    )
    links = relationship(
        "AmendmentLink",
        foreign_keys="AmendmentLink.amendment_id",
        back_populates="amendment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Amendment(id={self.amendment_id}, "
            f"ref='{self.amendment_reference}', "
            f"type={self.amendment_type}, "
            f"status={self.amendment_status})>"
        )


class AmendmentProgress(Base):
    __tablename__ = "amendment_progress"

    amendment_progress_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    amendment_id = Column(
        Integer, ForeignKey("amendments.amendment_id"), nullable=False
    )

    start_date = Column(DateTime, nullable=True)
    description = Column(Text, nullable=False)
    notes = Column(Text, nullable=True)

    # Audit fields
    created_by = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_by = Column(String(100), nullable=True)
    modified_on = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    amendment = relationship("Amendment", back_populates="progress_entries")

    def __repr__(self) -> str:
        return (
            f"<AmendmentProgress(id={self.amendment_progress_id}, "
            f"amendment_id={self.amendment_id}, "
            f"date={self.start_date})>"
        )


class AmendmentApplication(Base):
    __tablename__ = "amendment_applications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_id = Column(
        Integer, ForeignKey("amendments.amendment_id"), nullable=False
    )
    application_id = Column(
        Integer, ForeignKey("applications.application_id"), nullable=True
    )
    application_name = Column(String(100), nullable=False)
    reported_version = Column(String(50), nullable=True)
    applied_version = Column(String(50), nullable=True)
    development_status = Column(
        SQLEnum(DevelopmentStatus), nullable=True
    )

    # Relationships
    amendment = relationship("Amendment", back_populates="applications")
    application = relationship("Application")

    def __repr__(self) -> str:
        return (
            f"<AmendmentApplication(id={self.id}, "
            f"amendment_id={self.amendment_id}, "
            f"app='{self.application_name}')>"
        )


class AmendmentLink(Base):
    __tablename__ = "amendment_links"

    amendment_link_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    amendment_id = Column(
        Integer, ForeignKey("amendments.amendment_id"), nullable=False
    )
    linked_amendment_id = Column(
        Integer,
        ForeignKey("amendments.amendment_id", ondelete="CASCADE"),
        nullable=False,
    )
    link_type = Column(SQLEnum(LinkType), nullable=False, default=LinkType.RELATED)

    # Relationship
    amendment = relationship(
        "Amendment", foreign_keys=[amendment_id], back_populates="links"
    )

    def __repr__(self) -> str:
        return (
            f"<AmendmentLink(id={self.amendment_link_id}, "
            f"from={self.amendment_id}, "
            f"to={self.linked_amendment_id}, "
            f"type={self.link_type})>"
        )


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_name = Column(String(100), nullable=False, index=True)
    initials = Column(String(10), nullable=True)
    email = Column(String(150), nullable=True)
    windows_login = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)

    # Audit fields
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_on = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<Employee(id={self.employee_id}, "
            f"name='{self.employee_name}')>"
        )


class Application(Base):
    __tablename__ = "applications"

    application_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    application_name = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Audit fields
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_on = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    versions = relationship(
        "ApplicationVersion", back_populates="application", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Application(id={self.application_id}, "
            f"name='{self.application_name}')>"
        )


class ApplicationVersion(Base):
    __tablename__ = "application_versions"

    application_version_id = Column(
        Integer, primary_key=True, index=True, autoincrement=True
    )
    application_id = Column(
        Integer, ForeignKey("applications.application_id"), nullable=False
    )
    version = Column(String(50), nullable=False)
    released_date = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)

    # Audit fields
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_on = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationship
    application = relationship("Application", back_populates="versions")

    def __repr__(self) -> str:
        return (
            f"<ApplicationVersion(id={self.application_version_id}, "
            f"app_id={self.application_id}, "
            f"version='{self.version}')>"
        )
