from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from .database import Base


class AmendmentType(str, enum.Enum):
    FAULT = "Fault"
    ENHANCEMENT = "Enhancement"
    SUGGESTION = "Suggestion"


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


class QAStatus(str, enum.Enum):
    NOT_STARTED = "Not Started"
    ASSIGNED = "Assigned"
    IN_TESTING = "In Testing"
    BLOCKED = "Blocked"
    PASSED = "Passed"
    FAILED = "Failed"


class ExecutionStatus(str, enum.Enum):
    NOT_RUN = "Not Run"
    PASSED = "Passed"
    FAILED = "Failed"
    BLOCKED = "Blocked"
    SKIPPED = "Skipped"


class DefectStatus(str, enum.Enum):
    NEW = "New"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    VERIFIED = "Verified"
    CLOSED = "Closed"
    REOPENED = "Reopened"


class DefectSeverity(str, enum.Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class NotificationType(str, enum.Enum):
    QA_ASSIGNED = "QA Assigned"
    STATUS_CHANGED = "Status Changed"
    TEST_FAILED = "Test Failed"
    DEFECT_CREATED = "Defect Created"
    OVERDUE = "Overdue"
    SLA_BREACH = "SLA Breach"


class Priority(str, enum.Enum):
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Force(str, enum.Enum):
    # UK Police Forces
    AVON_AND_SOMERSET = "Avon And Somerset"
    BEDFORDSHIRE_CAMBRIDGESHIRE_HERTFORDSHIRE = "Bedfordshire, Cambridgeshire & Hertfordshire"
    BRITISH_TRANSPORT = "British Transport"
    CHESHIRE = "Cheshire"
    CLEVELAND = "Cleveland"
    CUMBRIA = "Cumbria"
    DERBYSHIRE = "Derbyshire"
    DEVON_AND_CORNWALL = "Devon And Cornwall"
    DURHAM = "Durham"
    ESSEX = "Essex"
    GLOUCESTERSHIRE = "Gloucestershire"
    GREATER_MANCHESTER = "Greater Manchester"
    GWENT = "Gwent"
    HAMPSHIRE = "Hampshire"
    KENT = "Kent"
    LANCASHIRE = "Lancashire"
    LEICESTERSHIRE = "Leicestershire"
    LINCOLNSHIRE = "Lincolnshire"
    MERSEYSIDE = "Merseyside"
    METROPOLITAN = "Metropolitan"
    NORFOLK_AND_SUFFOLK = "Norfolk & Suffolk"
    NORTH_WALES = "North Wales"
    NORTH_YORKSHIRE = "North Yorkshire"
    NORTHUMBRIA = "Northumbria"
    NOTTINGHAMSHIRE = "Nottinghamshire"
    POLICE_SCOTLAND = "Police Scotland"
    SOUTH_YORKSHIRE = "South Yorkshire"
    STAFFORDSHIRE = "Staffordshire"
    SURREY = "Surrey"
    SUSSEX = "Sussex"
    WARWICKSHIRE_WEST_MERCIA = "Warwickshire & West Mercia"
    WEST_MIDLANDS = "West Midlands"
    WEST_YORKSHIRE = "West Yorkshire"
    WILTSHIRE = "Wiltshire"

    # Organizations
    FIS = "FIS"
    HOME_OFFICE = "Home Office"
    IPCC = "IPCC"
    MOD = "MOD"
    NCUG = "NCUG"
    PIRC = "PIRC"
    UA = "UA"


class LinkType(str, enum.Enum):
    RELATED = "Related"
    DUPLICATE = "Duplicate"
    BLOCKS = "Blocks"
    BLOCKED_BY = "Blocked By"


class DocumentType(str, enum.Enum):
    TEST_PLAN = "Test Plan"
    SCREENSHOT = "Screenshot"
    SPECIFICATION = "Specification"
    OTHER = "Other"


class Amendment(Base):
    __tablename__ = "amendments"

    # Primary identification
    amendment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_reference = Column(String(50), unique=True, nullable=False, index=True)

    # Basic information
    amendment_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    amendment_status = Column(String(50), nullable=False, default="Open")
    development_status = Column(String(50), nullable=False, default="Not Started")
    priority = Column(String(50), nullable=False, default="Medium")
    force = Column(String(50), nullable=True)
    application = Column(String(100), nullable=True)
    version = Column(String(100), nullable=True, index=True)
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
    qa_status = Column(String(50), nullable=False, default="Not Started")
    qa_assigned_id = Column(Integer, nullable=True)
    qa_assigned_date = Column(DateTime, nullable=True)
    qa_started_date = Column(DateTime, nullable=True)
    qa_test_plan_check = Column(Boolean, default=False)
    qa_test_release_notes_check = Column(Boolean, default=False)
    qa_completed = Column(Boolean, default=False)
    qa_signature = Column(String(100), nullable=True)
    qa_completed_date = Column(DateTime, nullable=True)
    qa_notes = Column(Text, nullable=True)
    qa_test_plan_link = Column(String(500), nullable=True)
    qa_blocked_reason = Column(Text, nullable=True)
    qa_due_date = Column(DateTime, nullable=True)
    qa_sla_hours = Column(Integer, default=48, nullable=True)
    qa_overall_result = Column(String(50), nullable=True)

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
    documents = relationship(
        "AmendmentDocument", back_populates="amendment", cascade="all, delete-orphan"
    )
    # QA System relationships
    test_executions = relationship(
        "QATestExecution", back_populates="amendment", cascade="all, delete-orphan"
    )
    defects = relationship(
        "QADefect", back_populates="amendment", cascade="all, delete-orphan"
    )
    qa_history = relationship(
        "QAHistory", back_populates="amendment", cascade="all, delete-orphan"
    )
    qa_notifications = relationship(
        "QANotification", back_populates="amendment", cascade="all, delete-orphan"
    )
    qa_comments = relationship(
        "QAComment", back_populates="amendment", cascade="all, delete-orphan"
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
    development_status = Column(String(50), nullable=True)

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


class AmendmentDocument(Base):
    __tablename__ = "amendment_documents"

    document_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_id = Column(
        Integer, ForeignKey("amendments.amendment_id"), nullable=False
    )

    # Document information
    document_name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # Size in bytes
    mime_type = Column(String(100), nullable=True)
    document_type = Column(SQLEnum(DocumentType), nullable=False, default=DocumentType.OTHER)
    description = Column(Text, nullable=True)

    # Audit fields
    uploaded_by = Column(String(100), nullable=True)
    uploaded_on = Column(DateTime, default=func.now(), nullable=False)

    # Relationship
    amendment = relationship("Amendment", back_populates="documents")

    def __repr__(self) -> str:
        return (
            f"<AmendmentDocument(id={self.document_id}, "
            f"amendment_id={self.amendment_id}, "
            f"name='{self.document_name}')>"
        )


class Employee(Base):
    __tablename__ = "employees"

    employee_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_name = Column(String(100), nullable=False, index=True)
    initials = Column(String(10), nullable=True)
    email = Column(String(150), nullable=True, index=True)
    windows_login = Column(String(100), nullable=True, unique=True, index=True)
    is_active = Column(Boolean, default=True)

    # Authentication fields
    role = Column(String(20), nullable=False, default='User')  # 'Admin' or 'User'
    password_hash = Column(String(255), nullable=True)  # NULL for AD-only users
    last_login = Column(DateTime, nullable=True)

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


class QATestCase(Base):
    __tablename__ = "qa_test_cases"

    test_case_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    test_case_number = Column(String(20), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    test_type = Column(String(50), nullable=False, index=True)
    priority = Column(String(50), nullable=False, default="Medium", index=True)

    # Test details
    preconditions = Column(Text, nullable=True)
    test_steps = Column(Text, nullable=True)  # JSON array of steps
    expected_results = Column(Text, nullable=True)

    # Classification
    application_id = Column(Integer, ForeignKey("applications.application_id"), nullable=True)
    component = Column(String(100), nullable=True)
    tags = Column(Text, nullable=True)  # JSON array of tags

    # Status
    is_active = Column(Boolean, default=True, index=True)
    is_automated = Column(Boolean, default=False)
    automation_script = Column(Text, nullable=True)

    # Audit fields
    created_by = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_by = Column(String(100), nullable=True)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    application = relationship("Application")
    executions = relationship("QATestExecution", back_populates="test_case", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<QATestCase(id={self.test_case_id}, "
            f"number='{self.test_case_number}', "
            f"title='{self.title}')>"
        )


class QATestExecution(Base):
    __tablename__ = "qa_test_executions"

    execution_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_id = Column(Integer, ForeignKey("amendments.amendment_id", ondelete="CASCADE"), nullable=False, index=True)
    test_case_id = Column(Integer, ForeignKey("qa_test_cases.test_case_id"), nullable=False, index=True)
    executed_by_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True, index=True)

    # Execution details
    execution_status = Column(String(50), nullable=False, default="Not Run", index=True)
    executed_on = Column(DateTime, nullable=True, index=True)
    duration_minutes = Column(Integer, nullable=True)

    # Results
    actual_results = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    attachments = Column(Text, nullable=True)  # JSON array of attachment metadata

    # Environment
    test_environment = Column(String(100), nullable=True)
    build_version = Column(String(50), nullable=True)

    # Audit fields
    created_by = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_by = Column(String(100), nullable=True)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    amendment = relationship("Amendment", back_populates="test_executions")
    test_case = relationship("QATestCase", back_populates="executions")
    executed_by = relationship("Employee")
    defects = relationship("QADefect", back_populates="test_execution", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<QATestExecution(id={self.execution_id}, "
            f"amendment_id={self.amendment_id}, "
            f"status='{self.execution_status}')>"
        )


class QADefect(Base):
    __tablename__ = "qa_defects"

    defect_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    defect_number = Column(String(20), unique=True, nullable=False, index=True)
    amendment_id = Column(Integer, ForeignKey("amendments.amendment_id", ondelete="CASCADE"), nullable=False, index=True)
    test_execution_id = Column(Integer, ForeignKey("qa_test_executions.execution_id"), nullable=True, index=True)

    # Defect details
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(50), nullable=False, default="Medium", index=True)
    status = Column(String(50), nullable=False, default="New", index=True)

    # Reproduction
    steps_to_reproduce = Column(Text, nullable=True)
    actual_behavior = Column(Text, nullable=True)
    expected_behavior = Column(Text, nullable=True)

    # Assignment
    reported_by_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True, index=True)
    assigned_to_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True, index=True)

    # Resolution
    resolution = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    fixed_in_version = Column(String(50), nullable=True)

    # Dates
    reported_date = Column(DateTime, default=func.now(), nullable=False)
    assigned_date = Column(DateTime, nullable=True)
    resolved_date = Column(DateTime, nullable=True)
    closed_date = Column(DateTime, nullable=True)

    # Audit fields
    created_by = Column(String(100), nullable=True)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_by = Column(String(100), nullable=True)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    amendment = relationship("Amendment", back_populates="defects")
    test_execution = relationship("QATestExecution", back_populates="defects")
    reported_by = relationship("Employee", foreign_keys=[reported_by_id])
    assigned_to = relationship("Employee", foreign_keys=[assigned_to_id])
    notifications = relationship("QANotification", back_populates="defect", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"<QADefect(id={self.defect_id}, "
            f"number='{self.defect_number}', "
            f"title='{self.title}', "
            f"severity='{self.severity}')>"
        )


class QAHistory(Base):
    __tablename__ = "qa_history"

    history_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_id = Column(Integer, ForeignKey("amendments.amendment_id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False, index=True)

    # Change details
    field_name = Column(String(100), nullable=True)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    comment = Column(Text, nullable=True)

    # Audit
    changed_by_id = Column(Integer, ForeignKey("employees.employee_id"), nullable=True, index=True)
    changed_on = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    amendment = relationship("Amendment", back_populates="qa_history")
    changed_by = relationship("Employee")

    def __repr__(self) -> str:
        return (
            f"<QAHistory(id={self.history_id}, "
            f"amendment_id={self.amendment_id}, "
            f"action='{self.action}')>"
        )


class QANotification(Base):
    __tablename__ = "qa_notifications"

    notification_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False, index=True)

    # Content
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=True)

    # Links
    amendment_id = Column(Integer, ForeignKey("amendments.amendment_id", ondelete="CASCADE"), nullable=True, index=True)
    defect_id = Column(Integer, ForeignKey("qa_defects.defect_id", ondelete="CASCADE"), nullable=True, index=True)

    # Status
    is_read = Column(Boolean, default=False, index=True)
    is_email_sent = Column(Boolean, default=False)
    read_on = Column(DateTime, nullable=True)

    # Audit
    created_on = Column(DateTime, default=func.now(), nullable=False, index=True)

    # Relationships
    employee = relationship("Employee")
    amendment = relationship("Amendment", back_populates="qa_notifications")
    defect = relationship("QADefect", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<QANotification(id={self.notification_id}, "
            f"employee_id={self.employee_id}, "
            f"type='{self.notification_type}')>"
        )


class QAComment(Base):
    """QA Comment model for threaded discussions on amendments."""
    __tablename__ = "qa_comments"

    comment_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_id = Column(Integer, ForeignKey("amendments.amendment_id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)

    # Threading support
    parent_comment_id = Column(Integer, ForeignKey("qa_comments.comment_id", ondelete="CASCADE"), nullable=True, index=True)

    # Content
    comment_text = Column(Text, nullable=False)
    comment_type = Column(String(50), default="General", nullable=False)  # General/Issue/Resolution/Question

    # Metadata
    is_edited = Column(Boolean, default=False)
    created_on = Column(DateTime, default=func.now(), nullable=False, index=True)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    amendment = relationship("Amendment", back_populates="qa_comments")
    employee = relationship("Employee")
    # Self-referential relationship for threading
    parent = relationship("QAComment", remote_side=[comment_id], foreign_keys=[parent_comment_id], backref="replies")

    def __repr__(self) -> str:
        return (
            f"<QAComment(id={self.comment_id}, "
            f"amendment_id={self.amendment_id}, "
            f"employee_id={self.employee_id}, "
            f"type='{self.comment_type}')>"
        )


class AmendmentReferences(Base):
    __tablename__ = "amendment_references"

    id = Column(Integer, primary_key=True, index=True)
    bug_reference = Column(Integer, default=0, nullable=False)
    fault_reference = Column(Integer, default=0, nullable=False)
    enhancement_reference = Column(Integer, default=0, nullable=False)
    feature_reference = Column(Integer, default=0, nullable=False)
    suggestion_reference = Column(Integer, default=0, nullable=False)
    maintenance_reference = Column(Integer, default=0, nullable=False)
    documentation_reference = Column(Integer, default=0, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<AmendmentReferences(id={self.id}, "
            f"bug={self.bug_reference}, fault={self.fault_reference}, "
            f"enhancement={self.enhancement_reference})>"
        )


class ForceReference(Base):
    __tablename__ = "force_references"

    force_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    force_name = Column(String(100), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<ForceReference(id={self.force_id}, name='{self.force_name}')>"


class PriorityReference(Base):
    __tablename__ = "priority_references"

    priority_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    priority_name = Column(String(50), nullable=False, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PriorityReference(id={self.priority_id}, name='{self.priority_name}')>"


class StatusReference(Base):
    __tablename__ = "status_references"

    status_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    status_name = Column(String(50), nullable=False, unique=True, index=True)
    status_type = Column(String(20), nullable=False)  # 'amendment' or 'development'
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)
    created_on = Column(DateTime, default=func.now(), nullable=False)
    modified_on = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<StatusReference(id={self.status_id}, name='{self.status_name}', type='{self.status_type}')>"


# ==================== GitHub Issues Features ====================

class CommentMention(Base):
    """Track @ mentions in QA comments."""
    __tablename__ = "comment_mentions"

    mention_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey("qa_comments.comment_id", ondelete="CASCADE"), nullable=False, index=True)
    mentioned_employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)
    mentioned_by_employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False)

    created_on = Column(DateTime, default=func.now(), nullable=False)
    is_notified = Column(Boolean, default=False)

    # Relationships
    comment = relationship("QAComment", backref="mentions")
    mentioned_employee = relationship("Employee", foreign_keys=[mentioned_employee_id])
    mentioned_by = relationship("Employee", foreign_keys=[mentioned_by_employee_id])

    def __repr__(self) -> str:
        return (
            f"<CommentMention(id={self.mention_id}, "
            f"comment_id={self.comment_id}, "
            f"mentioned_employee_id={self.mentioned_employee_id})>"
        )


class AmendmentWatcher(Base):
    """Track users watching amendments for notifications."""
    __tablename__ = "amendment_watchers"
    __table_args__ = (
        UniqueConstraint('amendment_id', 'employee_id', name='uq_amendment_watcher'),
    )

    watcher_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    amendment_id = Column(Integer, ForeignKey("amendments.amendment_id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)

    watch_reason = Column(String(50), default="Manual")  # Manual/Mentioned/Assigned/Created/Participated
    is_watching = Column(Boolean, default=True)  # Allow mute

    created_on = Column(DateTime, default=func.now(), nullable=False)

    # Notification preferences
    notify_comments = Column(Boolean, default=True)
    notify_status_changes = Column(Boolean, default=True)
    notify_mentions = Column(Boolean, default=True)

    # Relationships
    amendment = relationship("Amendment", backref="watchers")
    employee = relationship("Employee")

    def __repr__(self) -> str:
        return (
            f"<AmendmentWatcher(id={self.watcher_id}, "
            f"amendment_id={self.amendment_id}, "
            f"employee_id={self.employee_id}, "
            f"watching={self.is_watching})>"
        )


class CommentReaction(Base):
    """Track emoji reactions on QA comments."""
    __tablename__ = "comment_reactions"
    __table_args__ = (
        UniqueConstraint('comment_id', 'employee_id', 'emoji', name='uq_comment_reaction'),
    )

    reaction_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comment_id = Column(Integer, ForeignKey("qa_comments.comment_id", ondelete="CASCADE"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.employee_id", ondelete="CASCADE"), nullable=False, index=True)

    emoji = Column(String(10), nullable=False)  # 👍 👎 ❤️ 🎉 😄 🚀

    created_on = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    comment = relationship("QAComment", backref="reactions")
    employee = relationship("Employee")

    def __repr__(self) -> str:
        return (
            f"<CommentReaction(id={self.reaction_id}, "
            f"comment_id={self.comment_id}, "
            f"employee_id={self.employee_id}, "
            f"emoji='{self.emoji}')>"
        )
