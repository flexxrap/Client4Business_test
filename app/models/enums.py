import enum


class SourceType(str, enum.Enum):
    PUBLICATION = "publication"
    SCENARIO = "scenario"
    EDIT = "edit"
    EXTERNAL = "external"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class DecisionAction(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    CANCEL = "cancel"
